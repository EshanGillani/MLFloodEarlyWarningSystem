import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.flood_model import FloodModel
from app.routers import demo, model_info, predict, weather
from app.services.database_service import DatabaseService
from app.services.ingestion_service import IngestionService
from app.services.prediction_service import PredictionService
from app.services.scheduler import PredictionScheduler
from app.services.weather_service import WeatherService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load model, connect DB, backfill, start scheduler. Shutdown: stop scheduler."""
    print("Starting Karachi Flood Early Warning System API...")

    # Initialize database
    db = DatabaseService()
    db.connect()

    # Initialize services
    weather_service = WeatherService()
    ingestion = IngestionService(weather_service, db)

    # Backfill / gap-fill weather observations
    if db.enabled:
        obs_count = db.get_observation_count()
        if obs_count == 0:
            print("No weather observations in DB — running initial backfill...")
            await asyncio.to_thread(ingestion.backfill_history)
        else:
            print(f"Found {obs_count} existing observations. Checking for gaps...")
            await asyncio.to_thread(ingestion.gap_fill)

    # Initialize model
    model = FloodModel()
    if not model.load():
        # No saved model — train from DB if enough data, otherwise legacy
        obs_count = db.get_observation_count() if db.enabled else 0
        if obs_count >= settings.min_observations_for_retrain:
            print(f"Training model from {obs_count} DB observations...")
            await asyncio.to_thread(model.train_from_db, db, "startup")
        else:
            print("Training model from legacy data...")
            await asyncio.to_thread(model.train)
        print(f"Model trained. Accuracy: {model.accuracy}%")
    else:
        print(f"Loaded saved model. Accuracy: {model.accuracy}% (source: {model._data_source})")

    prediction_service = PredictionService(model, weather_service, db)

    # Initialize and start background scheduler
    scheduler = PredictionScheduler(model, weather_service, db, ingestion)
    await scheduler.start()

    # Store in app state for dependency injection
    app.state.model = model
    app.state.weather = weather_service
    app.state.predictions = prediction_service
    app.state.db = db
    app.state.scheduler = scheduler
    app.state.ingestion = ingestion

    print("API ready.")
    yield

    # Shutdown
    await scheduler.stop()
    print("Shutting down.")


app = FastAPI(
    title="Karachi Flood Early Warning System API",
    description="ML-powered real-time flood risk prediction for Karachi, Pakistan",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/api", tags=["Predictions"])
app.include_router(weather.router, prefix="/api", tags=["Weather"])
app.include_router(model_info.router, prefix="/api", tags=["Model"])
app.include_router(demo.router, prefix="/api", tags=["Demo"])


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "karachi-flood-api",
        "database_connected": app.state.db.enabled if hasattr(app.state, "db") else False,
    }

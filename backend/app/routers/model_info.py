import asyncio

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/model/info")
async def get_model_info(request: Request):
    """Get model accuracy, feature importances, and training metadata."""
    model = request.app.state.model
    return model.get_info()


@router.post("/model/retrain")
async def retrain_model(request: Request):
    """Force retrain the model. Uses DB data if available, otherwise legacy."""
    model = request.app.state.model
    db = request.app.state.db
    obs_count = db.get_observation_count() if db.enabled else 0
    if obs_count >= 100:
        await asyncio.to_thread(model.train_from_db, db, "manual")
    else:
        await asyncio.to_thread(model.train)
    return model.get_info()

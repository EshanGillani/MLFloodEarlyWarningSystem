from __future__ import annotations

import asyncio
from datetime import datetime

from app.config import settings
from app.models.flood_model import FloodModel
from app.services.database_service import DatabaseService
from app.services.ingestion_service import IngestionService
from app.services.weather_service import WeatherService


class PredictionScheduler:
    """Background scheduler: ingest weather, predict, store, and periodically retrain."""

    def __init__(
        self,
        model: FloodModel,
        weather_service: WeatherService,
        db: DatabaseService,
        ingestion: IngestionService,
    ):
        self.model = model
        self.weather = weather_service
        self.db = db
        self.ingestion = ingestion
        self._task: asyncio.Task | None = None
        self._running = False
        self._retrain_counter = 0

    async def start(self) -> None:
        """Start the background prediction loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        print(
            f"Scheduler started — predictions every {settings.prediction_interval_minutes} minutes."
        )

    async def stop(self) -> None:
        """Stop the background prediction loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("Scheduler stopped.")

    async def _run_loop(self) -> None:
        """Main loop: ingest, predict, store, cleanup. Repeat."""
        # Run immediately on startup
        await self._run_once()

        while self._running:
            await asyncio.sleep(settings.prediction_interval_minutes * 60)
            if not self._running:
                break
            await self._run_once()

    async def _run_once(self) -> None:
        """Single prediction cycle."""
        try:
            # 1. Ingest current weather into observations table
            weather = await asyncio.to_thread(self.ingestion.ingest_current)
            if not weather:
                print(f"[{datetime.utcnow().isoformat()}] Scheduler: weather fetch failed, skipping.")
                return

            # 2. Run prediction
            prediction = self.model.predict(weather)

            # 3. Store prediction
            stored = self.db.store_prediction(weather, prediction)

            status_emoji = {"NORMAL": "G", "FLOOD WATCH": "Y", "EMERGENCY WARNING": "R"}
            marker = status_emoji.get(prediction["status"], "?")

            print(
                f"[{datetime.utcnow().isoformat()}] "
                f"[{marker}] {prediction['status']} "
                f"({prediction['confidence']:.0f}%) "
                f"P={weather['pressure']} R={weather['precipitation']} "
                f"T={weather.get('temperature', '?')} H={weather['humidity']} "
                f"{'-> stored' if stored else '-> in-memory only'}"
            )

            # 4. Cleanup old records
            self.db.cleanup_old_records()

            # 5. Periodic retraining
            self._retrain_counter += 1
            if self._retrain_counter >= settings.retrain_every_n_cycles:
                await self._retrain()
                self._retrain_counter = 0

        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Scheduler error: {e}")

    async def _retrain(self) -> None:
        """Retrain the model from accumulated DB observations."""
        obs_count = self.db.get_observation_count()
        if obs_count < settings.min_observations_for_retrain:
            print(f"Retrain skipped: only {obs_count} observations (need {settings.min_observations_for_retrain}).")
            return
        try:
            print(f"Retraining model on {obs_count} observations...")
            await asyncio.to_thread(self.model.train_from_db, self.db, "scheduled")
            print(f"Retrain complete. Accuracy: {self.model.accuracy}%")
        except Exception as e:
            print(f"Retrain error: {e}")

    async def run_once_manual(self) -> dict | None:
        """Run a single prediction cycle manually (for the /api/predict endpoint)."""
        try:
            weather = await asyncio.to_thread(self.weather.fetch_current)
            if not weather:
                return None

            prediction = self.model.predict(weather)
            self.db.store_prediction(weather, prediction)

            return {
                "weather": weather,
                "prediction": prediction,
                "last_updated": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"Manual prediction error: {e}")
            return None

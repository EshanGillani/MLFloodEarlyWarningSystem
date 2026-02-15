from __future__ import annotations

import asyncio
from datetime import datetime

from app.models.flood_model import FloodModel
from app.services.database_service import DatabaseService
from app.services.weather_service import WeatherService


class PredictionService:
    def __init__(
        self,
        model: FloodModel,
        weather_service: WeatherService,
        db: DatabaseService,
    ):
        self.model = model
        self.weather = weather_service
        self.db = db
        # In-memory fallback when database is not configured
        self.prediction_history: list[dict] = []

    async def get_current_prediction(self) -> dict | None:
        """Fetch current weather, predict, store, and return."""
        weather_data = await asyncio.to_thread(self.weather.fetch_current)
        if not weather_data:
            return None

        prediction = self.model.predict(weather_data)

        # Store in DB (non-blocking, don't fail if DB is down)
        self.db.store_prediction(weather_data, prediction)

        # Also keep in-memory fallback
        self._append_history(weather_data, prediction)

        return {
            "weather": weather_data,
            "prediction": prediction,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def get_prediction_history(self, hours: int = 48) -> list[dict]:
        """Get prediction history — from DB if available, otherwise from weather API."""
        # Try database first
        if self.db.enabled:
            db_history = self.db.get_history(hours=hours)
            if db_history:
                return db_history

        # Fallback: re-predict from weather API data
        weather_history = await asyncio.to_thread(self.weather.fetch_history, hours)

        results = []
        for entry in weather_history:
            weather_input = {
                "pressure": entry["pressure"],
                "precipitation": entry["precipitation"],
                "humidity": entry["humidity"],
                "temperature": entry.get("temperature"),
                "trend": 0.0,
            }
            prediction = self.model.predict(weather_input)
            results.append({
                "timestamp": entry["timestamp"],
                "pressure": entry["pressure"],
                "precipitation": entry["precipitation"],
                "humidity": entry["humidity"],
                "temperature": entry.get("temperature"),
                "trend": 0.0,
                "status": prediction["status"],
                "color": prediction["color"],
                "confidence": prediction["confidence"],
            })

        return results

    def _append_history(self, weather: dict, prediction: dict) -> None:
        self.prediction_history.append({
            "timestamp": weather["timestamp"],
            "pressure": weather["pressure"],
            "precipitation": weather["precipitation"],
            "humidity": weather["humidity"],
            "temperature": weather.get("temperature"),
            "trend": weather["trend"],
            "status": prediction["status"],
            "color": prediction["color"],
            "confidence": prediction["confidence"],
        })
        if len(self.prediction_history) > 200:
            self.prediction_history = self.prediction_history[-200:]

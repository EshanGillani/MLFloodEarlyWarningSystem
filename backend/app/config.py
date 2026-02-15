from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Karachi coordinates
    latitude: float = 24.8608
    longitude: float = 67.0104

    # Model parameters
    n_estimators: int = 100
    max_depth: int = 5
    flood_model_path: str = "app/data/flood_model.joblib"

    # API
    cors_origins: List[str] = [
        "http://localhost:3000",
        "https://*.vercel.app",
    ]
    cache_ttl_seconds: int = 1800

    # Open-Meteo
    past_days: int = 92
    api_url: str = "https://api.open-meteo.com/v1/forecast"

    # Database (PostgreSQL connection string)
    database_url: str = ""

    # Scheduler
    prediction_interval_minutes: int = 60
    history_retention_days: int = 90

    # Retraining
    retrain_every_n_cycles: int = 24
    min_observations_for_retrain: int = 100
    backfill_days: int = 92

    class Config:
        env_file = ".env"
        protected_namespaces = ("settings_",)


settings = Settings()

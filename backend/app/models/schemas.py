from __future__ import annotations

from pydantic import BaseModel


class WeatherData(BaseModel):
    pressure: float
    precipitation: float
    humidity: float
    trend: float
    timestamp: str
    data_hour_utc: str
    data_hour_pk: str


class FloodPrediction(BaseModel):
    prediction: int
    status: str
    color: str
    confidence: float


class PredictionResponse(BaseModel):
    weather: WeatherData
    prediction: FloodPrediction
    last_updated: str


class HistoryEntry(BaseModel):
    timestamp: str
    pressure: float
    precipitation: float
    humidity: float
    trend: float
    status: str
    color: str
    confidence: float


class WeatherHistoryEntry(BaseModel):
    timestamp: str
    pressure: float
    precipitation: float
    humidity: float


class ModelInfoResponse(BaseModel):
    accuracy: float
    feature_importances: dict[str, float]
    n_estimators: int
    max_depth: int
    training_timestamp: str | None
    training_samples: int
    features: list[str]


class DemoScenarioResponse(BaseModel):
    scenario: str
    weather: WeatherData
    prediction: FloodPrediction

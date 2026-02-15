from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from app.config import settings

STATUS_MAP = {
    0: ("NORMAL", "GREEN"),
    1: ("FLOOD WATCH", "YELLOW"),
    2: ("EMERGENCY WARNING", "RED"),
}

# Base features (always available for prediction)
FEATURE_NAMES_BASE = ["surface_pressure", "precipitation", "humidity", "pressure_trend"]

# Extended features (available when model trained from DB with rolling data)
FEATURE_NAMES_EXTENDED = [
    "surface_pressure", "precipitation", "humidity", "temperature",
    "pressure_trend_3h", "precip_rolling_6h", "precip_rolling_24h",
    "pressure_rolling_12h", "humidity_rolling_6h",
]


class FloodModel:
    def __init__(self):
        self.model: RandomForestClassifier | None = None
        self.accuracy: float = 0.0
        self.feature_importances: dict[str, float] = {}
        self.training_timestamp: str | None = None
        self.training_samples: int = 0
        self._active_features: list[str] = FEATURE_NAMES_BASE
        self._data_source: str = "legacy"
        self._obs_count: int = 0

    def train(self) -> None:
        """Legacy training: fetch from API + manual data + synthetic samples."""
        cache_session = requests_cache.CachedSession(".cache", expire_after=settings.cache_ttl_seconds)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        params_training = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": ["surface_pressure", "precipitation", "relative_humidity_2m"],
            "past_days": settings.past_days,
            "forecast_days": 0,
            "precipitation_unit": "inch",
        }

        responses = openmeteo.weather_api(settings.api_url, params_training)
        response = responses[0]
        hourly = response.Hourly()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            ),
            "api_pressure": hourly.Variables(0).ValuesAsNumpy(),
            "precipitation": hourly.Variables(1).ValuesAsNumpy(),
            "humidity": hourly.Variables(2).ValuesAsNumpy(),
        }
        api_df = pd.DataFrame(data=hourly_data)

        data_path = Path(__file__).parent.parent / "data" / "training_data.json"
        with open(data_path) as f:
            training_data = json.load(f)

        pressure_hpa = training_data["pressure_hpa"]
        start_date = datetime.strptime(training_data["start_date"], "%Y-%m-%d")
        manual_dates = [start_date + timedelta(days=i) for i in range(len(pressure_hpa))]

        manual_df = pd.DataFrame({
            "date_only": [d.date() for d in manual_dates],
            "surface_pressure": pressure_hpa,
        })

        api_df["date_only"] = api_df["date"].dt.date
        df = pd.merge(api_df, manual_df, on="date_only", how="inner")

        df["pressure_trend"] = df["surface_pressure"].diff(periods=3).fillna(0)
        df["flood_label"] = 0
        df.loc[
            (df["precipitation"].between(0.4, 0.9)) & (df["surface_pressure"] < 1005),
            "flood_label",
        ] = 1
        df.loc[
            (df["precipitation"] >= 1.0) | (df["surface_pressure"] <= 1000),
            "flood_label",
        ] = 2

        # Synthetic data
        np.random.seed(42)
        num_samples = 50
        normal_examples = pd.DataFrame({
            "surface_pressure": np.random.normal(1010, 3, num_samples),
            "precipitation": np.random.uniform(0, 0.3, num_samples),
            "humidity": np.random.normal(65, 8, num_samples),
            "pressure_trend": np.random.normal(0, 0.8, num_samples),
            "flood_label": 0,
        })
        watch_examples = pd.DataFrame({
            "surface_pressure": np.random.normal(1002, 2, num_samples),
            "precipitation": np.random.uniform(0.4, 0.9, num_samples),
            "humidity": np.random.normal(85, 5, num_samples),
            "pressure_trend": np.random.normal(-1.5, 0.6, num_samples),
            "flood_label": 1,
        })
        warning_examples = pd.DataFrame({
            "surface_pressure": np.random.normal(995, 3, num_samples),
            "precipitation": np.random.uniform(1.0, 3.5, num_samples),
            "humidity": np.random.normal(95, 3, num_samples),
            "pressure_trend": np.random.normal(-5.0, 1.5, num_samples),
            "flood_label": 2,
        })

        final_df = pd.concat(
            [
                df[["surface_pressure", "precipitation", "humidity", "pressure_trend", "flood_label"]],
                normal_examples, watch_examples, warning_examples,
            ],
            ignore_index=True,
        ).fillna(0)

        X = final_df[FEATURE_NAMES_BASE]
        y = final_df["flood_label"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(
            n_estimators=settings.n_estimators,
            max_depth=settings.max_depth,
            class_weight="balanced",
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        self.accuracy = round(self.model.score(X_test, y_test) * 100, 1)
        self.feature_importances = dict(zip(FEATURE_NAMES_BASE, [round(float(v), 4) for v in self.model.feature_importances_]))
        self.training_timestamp = datetime.utcnow().isoformat()
        self.training_samples = len(X_train) + len(X_test)
        self._active_features = FEATURE_NAMES_BASE
        self._data_source = "legacy"
        self._obs_count = 0

        self.save()

    def train_from_db(self, db, trigger: str = "scheduled") -> None:
        """Train from accumulated weather observations in the database."""
        rows = db.get_observations_for_training()
        if len(rows) < settings.min_observations_for_retrain:
            print(f"Only {len(rows)} observations — too few. Falling back to legacy train().")
            self.train()
            return

        df = pd.DataFrame(rows)

        # Try extended features first, fall back to base
        extended_cols = [c for c in FEATURE_NAMES_EXTENDED if c in df.columns]
        df_clean = df.dropna(subset=extended_cols)

        if len(df_clean) < settings.min_observations_for_retrain:
            # Not enough rows with all extended features — use base features
            base_remap = {
                "surface_pressure": "surface_pressure",
                "precipitation": "precipitation",
                "humidity": "humidity",
                "pressure_trend_3h": "pressure_trend_3h",
            }
            available = [c for c in base_remap.values() if c in df.columns]
            df_clean = df.dropna(subset=available)
            active_features = available
        else:
            active_features = extended_cols

        if len(df_clean) < 50:
            print("Insufficient data after filtering. Falling back to legacy train().")
            self.train()
            return

        # Add synthetic data (reduce as real data grows)
        real_count = len(df_clean)
        synthetic_per_class = max(10, min(50, 150 - real_count // 20))

        np.random.seed(42)
        synth_frames = []
        for label, p_mean, p_std, pr_lo, pr_hi, h_mean, h_std, t_mean, t_std, pt_mean, pt_std in [
            (0, 1010, 3, 0, 0.3, 65, 8, 30, 3, 0, 0.8),
            (1, 1002, 2, 0.4, 0.9, 85, 5, 32, 2, -1.5, 0.6),
            (2, 995, 3, 1.0, 3.5, 95, 3, 33, 2, -5.0, 1.5),
        ]:
            synth = {"flood_label": [label] * synthetic_per_class}
            for feat in active_features:
                if feat == "surface_pressure":
                    synth[feat] = np.random.normal(p_mean, p_std, synthetic_per_class)
                elif feat == "precipitation":
                    synth[feat] = np.random.uniform(pr_lo, pr_hi, synthetic_per_class)
                elif feat == "humidity":
                    synth[feat] = np.random.normal(h_mean, h_std, synthetic_per_class)
                elif feat == "temperature":
                    synth[feat] = np.random.normal(t_mean, t_std, synthetic_per_class)
                elif feat == "pressure_trend_3h":
                    synth[feat] = np.random.normal(pt_mean, pt_std, synthetic_per_class)
                elif feat == "precip_rolling_6h":
                    synth[feat] = np.random.uniform(pr_lo * 3, pr_hi * 3, synthetic_per_class)
                elif feat == "precip_rolling_24h":
                    synth[feat] = np.random.uniform(pr_lo * 12, pr_hi * 12, synthetic_per_class)
                elif feat == "pressure_rolling_12h":
                    synth[feat] = np.random.normal(p_mean, p_std * 0.5, synthetic_per_class)
                elif feat == "humidity_rolling_6h":
                    synth[feat] = np.random.normal(h_mean, h_std * 0.5, synthetic_per_class)
            synth_frames.append(pd.DataFrame(synth))

        final_df = pd.concat(
            [df_clean[active_features + ["flood_label"]]] + synth_frames,
            ignore_index=True,
        ).fillna(0)

        X = final_df[active_features]
        y = final_df["flood_label"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(
            n_estimators=settings.n_estimators,
            max_depth=settings.max_depth,
            class_weight="balanced",
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        self.accuracy = round(self.model.score(X_test, y_test) * 100, 1)
        self.feature_importances = dict(zip(active_features, [round(float(v), 4) for v in self.model.feature_importances_]))
        self.training_timestamp = datetime.utcnow().isoformat()
        self.training_samples = len(X_train) + len(X_test)
        self._active_features = active_features
        self._data_source = "database"
        self._obs_count = real_count

        self.save()

        # Log training event
        obs_start = df_clean["observed_at"].min() if "observed_at" in df_clean.columns else None
        obs_end = df_clean["observed_at"].max() if "observed_at" in df_clean.columns else None
        db.log_training(
            samples=self.training_samples,
            accuracy=self.accuracy,
            importances=self.feature_importances,
            obs_start=obs_start,
            obs_end=obs_end,
            trigger=trigger,
        )

        print(f"Trained from DB: {real_count} observations + {synthetic_per_class * 3} synthetic = {self.training_samples} total. Accuracy: {self.accuracy}%")

    def predict(self, weather: dict) -> dict:
        """Predict flood risk from weather data. Handles both base and extended feature sets."""
        features = []
        for feat in self._active_features:
            if feat == "surface_pressure":
                features.append(weather.get("pressure", 0))
            elif feat == "pressure_trend_3h":
                features.append(weather.get("trend", weather.get("pressure_trend_3h", 0)))
            elif feat in weather:
                features.append(weather[feat])
            else:
                features.append(0)

        input_df = pd.DataFrame([features], columns=self._active_features)

        pred = int(self.model.predict(input_df)[0])
        conf = float(self.model.predict_proba(input_df)[0][pred] * 100)
        status, color = STATUS_MAP[pred]

        return {
            "prediction": pred,
            "status": status,
            "color": color,
            "confidence": round(conf, 1),
        }

    def save(self) -> None:
        path = Path(settings.flood_model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "accuracy": self.accuracy,
                "feature_importances": self.feature_importances,
                "training_timestamp": self.training_timestamp,
                "training_samples": self.training_samples,
                "active_features": self._active_features,
                "data_source": self._data_source,
                "obs_count": self._obs_count,
            },
            path,
        )

    def load(self) -> bool:
        path = Path(settings.flood_model_path)
        if path.exists():
            data = joblib.load(path)
            self.model = data["model"]
            self.accuracy = data["accuracy"]
            self.feature_importances = data["feature_importances"]
            self.training_timestamp = data["training_timestamp"]
            self.training_samples = data["training_samples"]
            self._active_features = data.get("active_features", FEATURE_NAMES_BASE)
            self._data_source = data.get("data_source", "legacy")
            self._obs_count = data.get("obs_count", 0)
            return True
        return False

    def get_info(self) -> dict:
        return {
            "accuracy": self.accuracy,
            "feature_importances": self.feature_importances,
            "n_estimators": settings.n_estimators,
            "max_depth": settings.max_depth,
            "training_timestamp": self.training_timestamp,
            "training_samples": self.training_samples,
            "features": self._active_features,
            "data_source": self._data_source,
            "observation_count": self._obs_count,
        }

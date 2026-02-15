from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras

from app.config import settings

# Regex to parse postgresql://user:password@host:port/dbname
_DSN_RE = re.compile(
    r"^postgresql://(?P<user>[^:]+):(?P<password>.+)@(?P<host>[^:/?]+)(?::(?P<port>\d+))?/(?P<dbname>.+)$"
)


class DatabaseService:
    """Handles all PostgreSQL operations: weather observations, predictions, and training logs."""

    def __init__(self):
        self.conn = None
        self.enabled = bool(settings.database_url)

    # ── Connection ──────────────────────────────────────────────────

    def connect(self) -> None:
        if not self.enabled:
            print("DATABASE_URL not configured — running without persistent storage.")
            return
        try:
            m = _DSN_RE.match(settings.database_url)
            if not m:
                raise ValueError("Could not parse DATABASE_URL. Expected: postgresql://user:password@host:port/dbname")
            self.conn = psycopg2.connect(
                host=m.group("host"),
                port=int(m.group("port") or 5432),
                dbname=m.group("dbname"),
                user=m.group("user"),
                password=m.group("password"),
            )
            self.conn.autocommit = True
            self._ensure_tables()
            print("Connected to PostgreSQL.")
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            self.conn = None
            self.enabled = False

    def _ensure_tables(self) -> None:
        """Create all required tables if they don't exist."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            # 1. predictions table (existing)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    data_hour_utc TIMESTAMPTZ NOT NULL,
                    data_hour_pk TIMESTAMPTZ NOT NULL,
                    pressure DOUBLE PRECISION NOT NULL,
                    precipitation DOUBLE PRECISION NOT NULL,
                    humidity DOUBLE PRECISION NOT NULL,
                    pressure_trend DOUBLE PRECISION NOT NULL,
                    prediction INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    color TEXT NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictions_created_at
                ON predictions (created_at DESC);
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_data_hour
                ON predictions (data_hour_utc);
            """)

            # 2. weather_observations table (NEW)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weather_observations (
                    id BIGSERIAL PRIMARY KEY,
                    observed_at TIMESTAMPTZ NOT NULL,
                    surface_pressure DOUBLE PRECISION,
                    precipitation DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    temperature DOUBLE PRECISION,
                    source TEXT NOT NULL DEFAULT 'open-meteo',
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    pressure_trend_3h DOUBLE PRECISION,
                    precip_rolling_6h DOUBLE PRECISION,
                    precip_rolling_24h DOUBLE PRECISION,
                    pressure_rolling_12h DOUBLE PRECISION,
                    humidity_rolling_6h DOUBLE PRECISION,
                    flood_label INTEGER
                );
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_obs_observed_at
                ON weather_observations (observed_at);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_weather_obs_time_range
                ON weather_observations (observed_at DESC);
            """)

            # 3. model_training_log table (NEW)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS model_training_log (
                    id BIGSERIAL PRIMARY KEY,
                    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    training_samples INTEGER NOT NULL,
                    accuracy DOUBLE PRECISION NOT NULL,
                    feature_importances JSONB,
                    obs_date_start TIMESTAMPTZ,
                    obs_date_end TIMESTAMPTZ,
                    trigger TEXT NOT NULL DEFAULT 'scheduled'
                );
            """)

    # ── Weather Observations ────────────────────────────────────────

    def store_weather_observation(self, observed_at: str, pressure: float,
                                  precipitation: float, humidity: float,
                                  temperature: float | None = None,
                                  source: str = "open-meteo") -> bool:
        """Insert a single weather observation. ON CONFLICT DO NOTHING (idempotent)."""
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO weather_observations
                        (observed_at, surface_pressure, precipitation, humidity, temperature, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (observed_at) DO NOTHING;
                """, (observed_at, pressure, precipitation, humidity, temperature, source))
            return cur.rowcount > 0
        except Exception as e:
            print(f"Error storing observation: {e}")
            return False

    def store_weather_observations_batch(self, rows: list[dict]) -> int:
        """Batch insert weather observations. Returns count of new rows inserted."""
        if not self.conn or not rows:
            return 0
        try:
            values = [
                (r["observed_at"], r["surface_pressure"], r["precipitation"],
                 r["humidity"], r.get("temperature"), r.get("source", "open-meteo"))
                for r in rows
            ]
            with self.conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    """INSERT INTO weather_observations
                        (observed_at, surface_pressure, precipitation, humidity, temperature, source)
                    VALUES %s
                    ON CONFLICT (observed_at) DO NOTHING""",
                    values,
                    template="(%s, %s, %s, %s, %s, %s)",
                )
                return cur.rowcount
        except Exception as e:
            print(f"Error batch storing observations: {e}")
            return 0

    def get_latest_observation_time(self) -> datetime | None:
        """Return the most recent observed_at timestamp."""
        if not self.conn:
            return None
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT MAX(observed_at) FROM weather_observations;")
                row = cur.fetchone()
            return row[0] if row and row[0] else None
        except Exception as e:
            print(f"Error getting latest observation time: {e}")
            return None

    def get_observation_count(self) -> int:
        """Return total count of weather observations."""
        if not self.conn:
            return 0
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM weather_observations;")
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error counting observations: {e}")
            return 0

    def get_observations_for_training(self) -> list[dict]:
        """Fetch all labeled observations with derived features for model training."""
        if not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT observed_at, surface_pressure, precipitation, humidity,
                           temperature, pressure_trend_3h, precip_rolling_6h,
                           precip_rolling_24h, pressure_rolling_12h,
                           humidity_rolling_6h, flood_label
                    FROM weather_observations
                    WHERE flood_label IS NOT NULL
                    ORDER BY observed_at ASC;
                """)
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching training data: {e}")
            return []

    def get_observations_for_charts(self, hours: int = 48) -> list[dict]:
        """Fetch raw weather data for frontend charts."""
        if not self.conn:
            return []
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT observed_at, surface_pressure, precipitation,
                           humidity, temperature
                    FROM weather_observations
                    WHERE observed_at >= %s
                    ORDER BY observed_at ASC;
                """, (since,))
                rows = cur.fetchall()
            return [
                {
                    "timestamp": r["observed_at"].isoformat() if isinstance(r["observed_at"], datetime) else r["observed_at"],
                    "pressure": r["surface_pressure"],
                    "precipitation": r["precipitation"],
                    "humidity": r["humidity"],
                    "temperature": r["temperature"],
                }
                for r in rows
            ]
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            return []

    def update_derived_features(self) -> int:
        """Recompute rolling/derived features for rows where they are NULL."""
        if not self.conn:
            return 0
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    WITH computed AS (
                        SELECT id,
                            surface_pressure - LAG(surface_pressure, 3) OVER w AS pt3h,
                            SUM(precipitation) OVER (ORDER BY observed_at ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS pr6h,
                            SUM(precipitation) OVER (ORDER BY observed_at ROWS BETWEEN 23 PRECEDING AND CURRENT ROW) AS pr24h,
                            AVG(surface_pressure) OVER (ORDER BY observed_at ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS pavg12h,
                            AVG(humidity) OVER (ORDER BY observed_at ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS havg6h
                        FROM weather_observations
                        WINDOW w AS (ORDER BY observed_at)
                    )
                    UPDATE weather_observations o SET
                        pressure_trend_3h = c.pt3h,
                        precip_rolling_6h = c.pr6h,
                        precip_rolling_24h = c.pr24h,
                        pressure_rolling_12h = c.pavg12h,
                        humidity_rolling_6h = c.havg6h
                    FROM computed c
                    WHERE o.id = c.id AND o.pressure_trend_3h IS NULL;
                """)
                return cur.rowcount
        except Exception as e:
            print(f"Error updating derived features: {e}")
            return 0

    def apply_flood_labels(self) -> int:
        """Apply rule-based flood labels to unlabeled observations."""
        if not self.conn:
            return 0
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE weather_observations SET flood_label = CASE
                        WHEN precipitation >= 1.0 OR surface_pressure <= 1000 THEN 2
                        WHEN precipitation BETWEEN 0.4 AND 0.9 AND surface_pressure < 1005 THEN 1
                        ELSE 0
                    END
                    WHERE flood_label IS NULL;
                """)
                return cur.rowcount
        except Exception as e:
            print(f"Error applying labels: {e}")
            return 0

    def log_training(self, samples: int, accuracy: float, importances: dict,
                     obs_start: datetime | None, obs_end: datetime | None,
                     trigger: str = "scheduled") -> None:
        """Record a model training event."""
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO model_training_log
                        (training_samples, accuracy, feature_importances, obs_date_start, obs_date_end, trigger)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (samples, accuracy, json.dumps(importances), obs_start, obs_end, trigger))
        except Exception as e:
            print(f"Error logging training: {e}")

    # ── Predictions (existing methods) ──────────────────────────────

    def store_prediction(self, weather: dict, prediction: dict) -> bool:
        """Store a prediction in the database."""
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO predictions
                        (data_hour_utc, data_hour_pk, pressure, precipitation,
                         humidity, pressure_trend, prediction, status, color, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (data_hour_utc) DO UPDATE SET
                        pressure = EXCLUDED.pressure,
                        precipitation = EXCLUDED.precipitation,
                        humidity = EXCLUDED.humidity,
                        pressure_trend = EXCLUDED.pressure_trend,
                        prediction = EXCLUDED.prediction,
                        status = EXCLUDED.status,
                        color = EXCLUDED.color,
                        confidence = EXCLUDED.confidence;
                """, (
                    weather["data_hour_utc"],
                    weather["data_hour_pk"],
                    weather["pressure"],
                    weather["precipitation"],
                    weather["humidity"],
                    weather["trend"],
                    prediction["prediction"],
                    prediction["status"],
                    prediction["color"],
                    prediction["confidence"],
                ))
            return True
        except Exception as e:
            print(f"Error storing prediction: {e}")
            return False

    def get_history(self, hours: int = 48) -> list[dict]:
        """Get prediction history for the last N hours."""
        if not self.conn:
            return []
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM predictions
                    WHERE created_at >= %s
                    ORDER BY created_at ASC;
                """, (since,))
                rows = cur.fetchall()
            return [
                {
                    "timestamp": row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"],
                    "pressure": row["pressure"],
                    "precipitation": row["precipitation"],
                    "humidity": row["humidity"],
                    "trend": row["pressure_trend"],
                    "status": row["status"],
                    "color": row["color"],
                    "confidence": row["confidence"],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []

    def cleanup_old_records(self) -> int:
        """Delete old predictions and observations beyond retention period."""
        if not self.conn:
            return 0
        try:
            cutoff = (datetime.utcnow() - timedelta(days=settings.history_retention_days)).isoformat()
            total = 0
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM predictions WHERE created_at < %s;", (cutoff,))
                total += cur.rowcount
                cur.execute("DELETE FROM weather_observations WHERE observed_at < %s;", (cutoff,))
                total += cur.rowcount
            if total > 0:
                print(f"Cleaned up {total} records older than {settings.history_retention_days} days.")
            return total
        except Exception as e:
            print(f"Error cleaning up old records: {e}")
            return 0

    def get_latest_prediction(self) -> dict | None:
        """Get the most recent stored prediction."""
        if not self.conn:
            return None
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM predictions
                    ORDER BY created_at DESC LIMIT 1;
                """)
                row = cur.fetchone()
            if not row:
                return None
            created = row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"]
            return {
                "weather": {
                    "pressure": row["pressure"],
                    "precipitation": row["precipitation"],
                    "humidity": row["humidity"],
                    "trend": row["pressure_trend"],
                    "timestamp": created,
                    "data_hour_utc": row["data_hour_utc"].isoformat() if isinstance(row["data_hour_utc"], datetime) else row["data_hour_utc"],
                    "data_hour_pk": row["data_hour_pk"].isoformat() if isinstance(row["data_hour_pk"], datetime) else row["data_hour_pk"],
                },
                "prediction": {
                    "prediction": row["prediction"],
                    "status": row["status"],
                    "color": row["color"],
                    "confidence": row["confidence"],
                },
                "last_updated": created,
            }
        except Exception as e:
            print(f"Error fetching latest prediction: {e}")
            return None

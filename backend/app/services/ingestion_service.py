from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.services.database_service import DatabaseService
from app.services.weather_service import WeatherService


class IngestionService:
    """Orchestrates weather data collection: backfill, gap-fill, and hourly ingestion."""

    def __init__(self, weather_service: WeatherService, db: DatabaseService):
        self.weather = weather_service
        self.db = db

    def backfill_history(self) -> int:
        """Fetch up to backfill_days of hourly history and store in DB.
        Idempotent: skips rows that already exist."""
        rows = self.weather.fetch_history_bulk(days=settings.backfill_days)
        if not rows:
            print("Backfill: no data returned from Open-Meteo.")
            return 0

        count = self.db.store_weather_observations_batch(rows)
        print(f"Backfill: inserted {count} new observations ({len(rows)} fetched).")

        # Compute derived features and labels for the backfilled data
        updated = self.db.update_derived_features()
        labeled = self.db.apply_flood_labels()
        print(f"Backfill: computed features for {updated} rows, labeled {labeled} rows.")

        return count

    def ingest_current(self) -> dict | None:
        """Fetch the latest hourly observation and store it.
        Called by the scheduler every hour.
        Returns the weather dict or None on failure."""
        weather = self.weather.fetch_current()
        if not weather:
            return None

        # Store as observation
        self.db.store_weather_observation(
            observed_at=weather["data_hour_utc"],
            pressure=weather["pressure"],
            precipitation=weather["precipitation"],
            humidity=weather["humidity"],
            temperature=weather.get("temperature"),
        )

        # Update derived features (recalculates for new row and any NULLs)
        self.db.update_derived_features()
        self.db.apply_flood_labels()

        return weather

    def gap_fill(self) -> int:
        """Check the latest observation in DB, fetch any missing hours up to now.
        Called on startup after initial backfill. Returns count of new rows."""
        latest = self.db.get_latest_observation_time()

        if latest is None:
            # No data at all — backfill will handle it
            return 0

        now = datetime.now(timezone.utc)
        # Make latest timezone-aware if it isn't
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        hours_missing = (now - latest).total_seconds() / 3600

        if hours_missing <= 1:
            return 0  # Up to date

        # Fetch the missing range
        start_date = latest.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        rows = self.weather.fetch_range(start_date, end_date)
        if not rows:
            return 0

        count = self.db.store_weather_observations_batch(rows)
        if count > 0:
            self.db.update_derived_features()
            self.db.apply_flood_labels()
            print(f"Gap-fill: inserted {count} missing observations.")

        return count

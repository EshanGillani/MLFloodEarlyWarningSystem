from __future__ import annotations

import traceback
from datetime import datetime

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from app.config import settings

# All hourly fields we fetch from Open-Meteo
_HOURLY_FIELDS = [
    "surface_pressure",
    "precipitation",
    "relative_humidity_2m",
    "temperature_2m",
]


class WeatherService:
    def __init__(self):
        cache_session = requests_cache.CachedSession(".cache", expire_after=settings.cache_ttl_seconds)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

    def fetch_current(self) -> dict | None:
        """Fetch current weather for Karachi using the closest available hour."""
        params = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": _HOURLY_FIELDS,
            "forecast_days": 1,
            "precipitation_unit": "inch",
        }

        try:
            responses = self.client.weather_api(settings.api_url, params)
            response = responses[0]
            hourly = response.Hourly()

            pressure_array = hourly.Variables(0).ValuesAsNumpy()
            precip_array = hourly.Variables(1).ValuesAsNumpy()
            humidity_array = hourly.Variables(2).ValuesAsNumpy()
            temp_array = hourly.Variables(3).ValuesAsNumpy()

            data_times = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )

            now = pd.Timestamp.utcnow()
            time_diffs = np.abs((data_times - now).total_seconds())
            idx = int(np.argmin(time_diffs))

            pk_time = data_times[idx] + pd.Timedelta(hours=5)

            pressure = float(pressure_array[idx])
            precip = float(precip_array[idx])
            humidity = float(humidity_array[idx])
            temperature = float(temp_array[idx])

            if idx + 3 < len(pressure_array):
                trend = float(pressure_array[idx + 3] - pressure_array[idx])
            else:
                trend = 0.0

            return {
                "pressure": round(pressure, 2),
                "precipitation": round(precip, 4),
                "humidity": round(humidity, 1),
                "temperature": round(temperature, 1),
                "trend": round(trend, 2),
                "timestamp": datetime.now().isoformat(),
                "data_hour_utc": str(data_times[idx]),
                "data_hour_pk": str(pk_time),
            }

        except Exception as e:
            print("Error fetching weather:", e)
            traceback.print_exc()
            return None

    def fetch_history(self, hours: int = 48) -> list[dict]:
        """Fetch recent hourly weather data for charting."""
        params = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": _HOURLY_FIELDS,
            "past_days": 2,
            "forecast_days": 1,
            "precipitation_unit": "inch",
        }

        try:
            responses = self.client.weather_api(settings.api_url, params)
            response = responses[0]
            hourly = response.Hourly()

            pressure_array = hourly.Variables(0).ValuesAsNumpy()
            precip_array = hourly.Variables(1).ValuesAsNumpy()
            humidity_array = hourly.Variables(2).ValuesAsNumpy()
            temp_array = hourly.Variables(3).ValuesAsNumpy()

            data_times = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )

            result = []
            limit = min(hours, len(data_times))
            for i in range(max(0, len(data_times) - limit), len(data_times)):
                result.append({
                    "timestamp": str(data_times[i]),
                    "pressure": round(float(pressure_array[i]), 2),
                    "precipitation": round(float(precip_array[i]), 4),
                    "humidity": round(float(humidity_array[i]), 1),
                    "temperature": round(float(temp_array[i]), 1),
                })

            return result

        except Exception as e:
            print("Error fetching weather history:", e)
            traceback.print_exc()
            return []

    def fetch_history_bulk(self, days: int = 92) -> list[dict]:
        """Fetch up to `days` of hourly history for backfill into DB."""
        params = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": _HOURLY_FIELDS,
            "past_days": days,
            "forecast_days": 0,
            "precipitation_unit": "inch",
        }

        try:
            responses = self.client.weather_api(settings.api_url, params)
            response = responses[0]
            hourly = response.Hourly()

            pressure_array = hourly.Variables(0).ValuesAsNumpy()
            precip_array = hourly.Variables(1).ValuesAsNumpy()
            humidity_array = hourly.Variables(2).ValuesAsNumpy()
            temp_array = hourly.Variables(3).ValuesAsNumpy()

            data_times = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )

            result = []
            for i in range(len(data_times)):
                result.append({
                    "observed_at": str(data_times[i]),
                    "surface_pressure": round(float(pressure_array[i]), 2),
                    "precipitation": round(float(precip_array[i]), 4),
                    "humidity": round(float(humidity_array[i]), 1),
                    "temperature": round(float(temp_array[i]), 1),
                    "source": "open-meteo",
                })

            return result

        except Exception as e:
            print("Error fetching bulk weather history:", e)
            traceback.print_exc()
            return []

    def fetch_range(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch hourly data for a specific date range (YYYY-MM-DD strings)."""
        params = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": _HOURLY_FIELDS,
            "start_date": start_date,
            "end_date": end_date,
            "precipitation_unit": "inch",
        }

        try:
            responses = self.client.weather_api(settings.api_url, params)
            response = responses[0]
            hourly = response.Hourly()

            pressure_array = hourly.Variables(0).ValuesAsNumpy()
            precip_array = hourly.Variables(1).ValuesAsNumpy()
            humidity_array = hourly.Variables(2).ValuesAsNumpy()
            temp_array = hourly.Variables(3).ValuesAsNumpy()

            data_times = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )

            result = []
            for i in range(len(data_times)):
                result.append({
                    "observed_at": str(data_times[i]),
                    "surface_pressure": round(float(pressure_array[i]), 2),
                    "precipitation": round(float(precip_array[i]), 4),
                    "humidity": round(float(humidity_array[i]), 1),
                    "temperature": round(float(temp_array[i]), 1),
                    "source": "open-meteo",
                })

            return result

        except Exception as e:
            print("Error fetching weather range:", e)
            traceback.print_exc()
            return []

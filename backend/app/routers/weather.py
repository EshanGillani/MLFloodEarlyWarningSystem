import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


@router.get("/weather/current")
async def get_current_weather(request: Request):
    """Get raw current weather data for Karachi."""
    weather_service = request.app.state.weather
    data = await asyncio.to_thread(weather_service.fetch_current)
    if not data:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    return data


@router.get("/weather/history")
async def get_weather_history(request: Request, hours: int = 48):
    """Get hourly weather history for charts (from Open-Meteo API)."""
    weather_service = request.app.state.weather
    return await asyncio.to_thread(weather_service.fetch_history, hours)


@router.get("/weather/observations")
async def get_weather_observations(request: Request, hours: int = Query(48, ge=1, le=720)):
    """Get stored weather observations from the time-series database.
    Returns hourly pressure, precipitation, temperature, and humidity."""
    db = request.app.state.db
    if not db.enabled:
        # Fall back to Open-Meteo API if no database
        weather_service = request.app.state.weather
        return await asyncio.to_thread(weather_service.fetch_history, hours)
    return db.get_observations_for_charts(hours=hours)

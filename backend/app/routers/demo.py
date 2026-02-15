from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

DEMO_SCENARIOS = {
    "normal": {
        "pressure": 1012.5,
        "precipitation": 0.05,
        "humidity": 60.0,
        "trend": 0.2,
    },
    "watch": {
        "pressure": 1002.3,
        "precipitation": 0.65,
        "humidity": 87.0,
        "trend": -1.8,
    },
    "emergency": {
        "pressure": 993.1,
        "precipitation": 2.5,
        "humidity": 96.0,
        "trend": -5.5,
    },
}


@router.get("/demo/scenarios")
async def list_scenarios():
    """List available demo scenarios."""
    return {"scenarios": list(DEMO_SCENARIOS.keys())}


@router.get("/demo/scenario/{name}")
async def get_scenario(name: str, request: Request):
    """Get simulated weather and prediction for a demo scenario."""
    if name not in DEMO_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")

    weather_values = DEMO_SCENARIOS[name]
    now = datetime.utcnow().isoformat()

    weather_data = {
        **weather_values,
        "timestamp": now,
        "data_hour_utc": now,
        "data_hour_pk": now,
    }

    model = request.app.state.model
    prediction = model.predict(weather_values)

    return {
        "scenario": name,
        "weather": weather_data,
        "prediction": prediction,
        "last_updated": now,
    }

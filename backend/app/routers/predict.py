from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/predict")
async def get_current_prediction(request: Request):
    """Get current live flood prediction with weather data."""
    prediction_service = request.app.state.predictions
    result = await prediction_service.get_current_prediction()
    if not result:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    return result


@router.get("/predict/history")
async def get_prediction_history(request: Request, hours: int = 48):
    """Get historical predictions for charting."""
    prediction_service = request.app.state.predictions
    return await prediction_service.get_prediction_history(hours=hours)

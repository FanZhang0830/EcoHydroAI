# app/api/routes/weather.py

from fastapi import APIRouter, HTTPException

from services.weather_service import get_weather_for_watershed
from app.models.weather import WeatherResponse


router = APIRouter(
    prefix="/api/v1/watersheds",
    tags=["Weather"]
)


@router.get("/{watershed_id}/weather", response_model=WeatherResponse)
def get_weather(watershed_id: str):
    """
    Return a mock 3-day weather forecast for a watershed.
    """

    result = get_weather_for_watershed(watershed_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Watershed not found: {watershed_id}"
        )

    return result
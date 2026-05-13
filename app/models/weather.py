# app/models/weather.py

from pydantic import BaseModel
from typing import List


class DailyForecast(BaseModel):
    date: str
    temperature_max_c: float
    temperature_min_c: float
    precipitation_mm: float
    summary: str


class Coordinates(BaseModel):
    lat: float
    lon: float


class WeatherResponse(BaseModel):
    watershed_id: str
    watershed_name: str
    location: Coordinates
    forecast: List[DailyForecast]
    chart_base64: str
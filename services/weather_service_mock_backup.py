# services/weather_service.py
# This is a mock weather forecast now
# Will be replaced by Open-Meteo api in the future

from datetime import date, timedelta
from io import BytesIO
import base64

import matplotlib.pyplot as plt

from services.watershed_service import get_subwatershed_summary


def _build_mock_forecast():
    """
    Build a simple 3-day mock weather forecast starting from today.
    """

    today = date.today()

    forecast = [
        {
            "date": (today + timedelta(days=0)).isoformat(),
            "temperature_max_c": 19.0,
            "temperature_min_c": 8.0,
            "precipitation_mm": 2.5,
            "summary": "Light rain possible",
        },
        {
            "date": (today + timedelta(days=1)).isoformat(),
            "temperature_max_c": 21.0,
            "temperature_min_c": 10.0,
            "precipitation_mm": 6.8,
            "summary": "Moderate rain expected",
        },
        {
            "date": (today + timedelta(days=2)).isoformat(),
            "temperature_max_c": 17.5,
            "temperature_min_c": 7.5,
            "precipitation_mm": 1.2,
            "summary": "Mostly cloudy with light showers",
        },
    ]

    return forecast


def _generate_weather_chart_base64(forecast: list[dict]) -> str:
    """
    Generate a simple time series chart with:
    - max temperature
    - min temperature
    - precipitation

    The chart is returned as a base64-encoded PNG string.
    """

    dates = [item["date"] for item in forecast]
    temp_max = [item["temperature_max_c"] for item in forecast]
    temp_min = [item["temperature_min_c"] for item in forecast]
    precip = [item["precipitation_mm"] for item in forecast]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))

    # Temperature lines on primary y-axis
    ax1.plot(dates, temp_max, marker="o", label="Max Temp (°C)")
    ax1.plot(dates, temp_min, marker="o", label="Min Temp (°C)")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Temperature (°C)")
    ax1.tick_params(axis="x", rotation=30)

    # Precipitation bars on secondary y-axis
    ax2 = ax1.twinx()
    ax2.bar(dates, precip, alpha=0.35, label="Precipitation (mm)")
    ax2.set_ylabel("Precipitation (mm)")

    # Combine legends from both axes
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.title("3-Day Weather Forecast")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")

    return encoded


def get_mock_weather_for_watershed(watershed_id: str) -> dict | None:
    """
    Return a mock 3-day weather forecast and chart for a given watershed.
    """

    watershed = get_subwatershed_summary(watershed_id)

    if watershed is None:
        return None

    forecast = _build_mock_forecast()
    chart_base64 = _generate_weather_chart_base64(forecast)

    return {
        "watershed_id": watershed["id"],
        "watershed_name": watershed["name"],
        "location": watershed["centroid"],
        "forecast": forecast,
        "chart_base64": chart_base64,
    }
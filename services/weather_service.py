# services/weather_service.py

from io import BytesIO
import base64

import requests
import matplotlib.pyplot as plt

from services.watershed_service import get_subwatershed_summary


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _build_summary(precipitation_mm: float, temp_max_c: float, temp_min_c: float) -> str:
    """
    Build a simple human-readable weather summary.
    """

    if precipitation_mm >= 15:
        rain_text = "Heavy rain expected"
    elif precipitation_mm >= 5:
        rain_text = "Moderate rain expected"
    elif precipitation_mm > 0:
        rain_text = "Light precipitation possible"
    else:
        rain_text = "No precipitation expected"

    return f"{rain_text}; temperature range {temp_min_c:.1f}–{temp_max_c:.1f} °C"


def _fetch_open_meteo_forecast(lat: float, lon: float) -> list[dict]:
    """
    Fetch a 3-day daily weather forecast from Open-Meteo.

    Returns:
        A list of daily forecast dictionaries.
    """

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 3,
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    daily = data.get("daily", {})

    dates = daily.get("time", [])
    temp_max_values = daily.get("temperature_2m_max", [])
    temp_min_values = daily.get("temperature_2m_min", [])
    precip_values = daily.get("precipitation_sum", [])

    forecast = []

    for date_str, temp_max, temp_min, precip in zip(
        dates,
        temp_max_values,
        temp_min_values,
        precip_values,
    ):
        temp_max = float(temp_max) if temp_max is not None else 0.0
        temp_min = float(temp_min) if temp_min is not None else 0.0
        precip = float(precip) if precip is not None else 0.0

        forecast.append(
            {
                "date": date_str,
                "temperature_max_c": round(temp_max, 1),
                "temperature_min_c": round(temp_min, 1),
                "precipitation_mm": round(precip, 1),
                "summary": _build_summary(
                    precipitation_mm=precip,
                    temp_max_c=temp_max,
                    temp_min_c=temp_min,
                ),
            }
        )

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


def get_weather_for_watershed(watershed_id: str) -> dict | None:
    """
    Return a real 3-day Open-Meteo weather forecast and chart
    for a given watershed.

    Note:
        The function name is kept for now so the existing API route
        does not need to be changed immediately.
    """

    watershed = get_subwatershed_summary(watershed_id)

    if watershed is None:
        return None

    lat = watershed["centroid"]["lat"]
    lon = watershed["centroid"]["lon"]

    forecast = _fetch_open_meteo_forecast(
        lat=lat,
        lon=lon,
    )

    chart_base64 = _generate_weather_chart_base64(forecast)

    return {
        "watershed_id": watershed["id"],
        "watershed_name": watershed["name"],
        "location": watershed["centroid"],
        "forecast": forecast,
        "chart_base64": chart_base64,
    }
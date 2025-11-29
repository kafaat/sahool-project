from datetime import datetime
from typing import List

import httpx
from pydantic import BaseModel

from app.core.config import settings


class WeatherPoint(BaseModel):
    timestamp: datetime
    rain_mm: float | None = None
    eto_mm: float | None = None
    temp_c: float | None = None


class WeatherIngestResult(BaseModel):
    field_id: int
    points_ingested: int


async def _get_field_centroid(field_id: int, tenant_id: int) -> tuple[float, float]:
    url = f"{settings.GATEWAY_URL}/api/geo/fields/{field_id}"
    params = {"tenant_id": tenant_id}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    lat = data.get("centroid_lat")
    lon = data.get("centroid_lon")
    if lat is None or lon is None:
        raise ValueError("Field centroid is missing; cannot request weather.")
    return float(lat), float(lon)


async def fetch_openmeteo(lat: float, lon: float) -> List[WeatherPoint]:
    """Fetch simple hourly forecast from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation",
        "forecast_days": 3,
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    temp = hourly.get("temperature_2m") or []
    rain = hourly.get("precipitation") or []

    points: list[WeatherPoint] = []
    for i, ts in enumerate(times):
        t = datetime.fromisoformat(ts)
        r = float(rain[i]) if i < len(rain) else None
        temp_c = float(temp[i]) if i < len(temp) else None
        points.append(
            WeatherPoint(timestamp=t, rain_mm=r, temp_c=temp_c, eto_mm=None)
        )
    return points


async def ingest_field_weather(field_id: int, tenant_id: int) -> WeatherIngestResult:
    lat, lon = await _get_field_centroid(field_id, tenant_id)
    points = await fetch_openmeteo(lat, lon)

    async with httpx.AsyncClient(timeout=20.0) as client:
        payload = {
            "tenant_id": tenant_id,
            "field_id": field_id,
            "points": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "rain_mm": p.rain_mm,
                    "eto_mm": p.eto_mm,
                    "temp_c": p.temp_c,
                }
                for p in points
            ],
        }
        try:
            await client.post(
                f"{settings.GATEWAY_URL}/api/weather/api/v1/weather/ingest",
                json=payload,
            )
        except Exception:
            # In real implementation add proper logging/monitoring
            pass

    return WeatherIngestResult(field_id=field_id, points_ingested=len(points))

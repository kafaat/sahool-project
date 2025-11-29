from typing import List
from fastapi import APIRouter, Query, HTTPException
import httpx
from app.core.config import settings
from app.schemas.timeline import FieldTimelinePoint, FieldTimelineResponse

router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])


async def _fetch_weather_points(tenant_id: int, field_id: int) -> list[dict]:
    url = f"{settings.GATEWAY_URL}/api/weather/api/v1/weather/forecast"
    params = {"tenant_id": tenant_id, "field_id": field_id, "hours_ahead": 72}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
    if resp.status_code != 200:
        return []
    data = resp.json()
    points = data.get("points") or []
    return points


@router.get("/field/{field_id}", response_model=FieldTimelineResponse)
async def get_field_timeline(
    field_id: int,
    tenant_id: int = Query(...),
):
    """Aggregate a simple timeline for a field.

    Currently this builds the timeline primarily from the weather forecast
    (timestamp, eto_mm, rain_mm). NDVI values are left as None for now, and
    can be filled later once a numeric NDVI time-series is available.
    """
    weather_points = await _fetch_weather_points(tenant_id, field_id)

    timeline_points: list[FieldTimelinePoint] = []

    for p in weather_points:
        ts = p.get("timestamp")
        if not ts:
            continue
        eto = p.get("eto_mm")
        rain = p.get("rain_mm")
        timeline_points.append(
            FieldTimelinePoint(
                timestamp=ts,
                ndvi=None,
                eto=eto,
                rain_mm=rain,
            )
        )

    return FieldTimelineResponse(
        tenant_id=tenant_id,
        field_id=field_id,
        timeline=timeline_points,
    )

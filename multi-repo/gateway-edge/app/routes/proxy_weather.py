from fastapi import APIRouter, Request
from ..core.config import settings
from ..core.http_client import get_json, post_json
from ..core.ratelimit import rate_limit
from ..core.abac import abac_guard

router=APIRouter(prefix='/v1/weather', tags=['proxy.weather'])

@router.get("/forecast")
async def forecast_weather(request: Request, tenant_id: str, field_id: str|None=None):
    rate_limit(request)
    return await get_json(f"{settings.WEATHER_CORE_URL}/v1/weather/forecast", params={"tenant_id":tenant_id,"field_id":field_id})

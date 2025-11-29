
import httpx
from fastapi import APIRouter, Request
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api")

SERVICE_MAP = {
    "platform": settings.PLATFORM_URL,
    "geo": settings.GEO_URL,
    "imagery": settings.IMAGERY_URL,
    "soil": settings.SOIL_URL,
    "weather": settings.WEATHER_URL,
    "alerts": settings.ALERTS_URL,
    "analytics": settings.ANALYTICS_URL,
    "timeline": settings.TIMELINE_URL,
    "agent": "http://sahool-agent-ai:9010",
}

@router.api_route("/{service}/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        return {"error": "service not found"}

    url = f"{SERVICE_MAP[service]}/{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            url,
            params=dict(request.query_params),
            json=await request.json() if request.method in ["POST","PUT"] else None
        )
    return resp.json()

import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Request, Header, HTTPException

from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api")

SERVICE_MAP: Dict[str, str] = {
    "platform": settings.PLATFORM_URL,
    "geo": settings.GEO_URL,
    "imagery": settings.IMAGERY_URL,
    "soil": settings.SOIL_URL,
    "weather": settings.WEATHER_URL,
    "alerts": settings.ALERTS_URL,
    "analytics": settings.ANALYTICS_URL,
    "agent": settings.AGENT_URL,
}


def _check_api_key(x_api_key: str | None) -> None:
    """تحقق بسيط من X-API-Key إذا كانت AUTH_ENABLED=True."""
    if not settings.AUTH_ENABLED:
        # في وضع التطوير لا نفرض المفتاح
        return
    if not x_api_key or x_api_key not in settings.API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(
    service: str,
    path: str,
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail="Service not found")

    _check_api_key(x_api_key)

    base_url = SERVICE_MAP[service].rstrip("/")
    url = f"{base_url}/{path.lstrip('/')}"
    method = request.method.upper()

    # Read body safely
    body_bytes = await request.body()
    json_body = None
    if body_bytes:
        try:
            json_body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            json_body = None

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.request(
            method,
            url,
            params=dict(request.query_params),
            json=json_body if method in {"POST", "PUT", "PATCH"} else None,
            headers={k: v for k, v in request.headers.items() if k.lower() not in {"host"}},
        )

    # Forward status code and JSON body (if any)
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "raw": resp.text}
    return {"status_code": resp.status_code, "raw": resp.text}

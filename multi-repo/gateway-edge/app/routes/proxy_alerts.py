from fastapi import APIRouter, Request
from ..core.config import settings
from ..core.http_client import get_json, post_json
from ..core.ratelimit import rate_limit
from ..core.abac import abac_guard

router=APIRouter(prefix='/v1/alerts', tags=['proxy.alerts'])

@router.get("/recent")
async def recent_alerts(request: Request, tenant_id: str, hours:int=72):
    rate_limit(request)
    return await get_json(f"{settings.ALERTS_CORE_URL}/v1/alerts/recent", params={"tenant_id":tenant_id,"hours":hours})

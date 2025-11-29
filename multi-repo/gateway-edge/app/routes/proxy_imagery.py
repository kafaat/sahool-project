from fastapi import APIRouter, Request
from ..core.config import settings
from ..core.http_client import get_json, post_json
from ..core.ratelimit import rate_limit
from ..core.abac import abac_guard

router=APIRouter(prefix='/v1/imagery', tags=['proxy.imagery'])

@router.get("/fields/{field_id}/indices/latest")
async def latest_indices(field_id: str, request: Request, tenant_id: str):
    rate_limit(request); abac_guard(request,"imagery:latest","field")
    return await get_json(f"{settings.IMAGERY_CORE_URL}/fields/{field_id}/indices/latest", params={"tenant_id": tenant_id})
@router.get("/fields/{field_id}/indices/timeline")
async def indices_timeline(field_id: str, request: Request, tenant_id: str, from_date: str, to_date: str):
    rate_limit(request)
    return await get_json(f"{settings.IMAGERY_CORE_URL}/fields/{field_id}/indices/timeline",
                          params={"tenant_id": tenant_id,"from_date":from_date,"to_date":to_date})

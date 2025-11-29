from fastapi import APIRouter, Request
from ..core.config import settings
from ..core.http_client import get_json, post_json
from ..core.ratelimit import rate_limit
from ..core.abac import abac_guard

router=APIRouter(prefix='/v1/fields', tags=['proxy.geo'])

@router.get("")
async def list_fields(request: Request, tenant_id: str):
    rate_limit(request); abac_guard(request,"fields:list","tenant")
    return await get_json(f"{settings.GEO_CORE_URL}/v1/fields", params={"tenant_id": tenant_id})

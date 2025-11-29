from fastapi import APIRouter, Request
from ..core.config import settings
from ..core.http_client import get_json, post_json
from ..core.ratelimit import rate_limit
from ..core.abac import abac_guard

router=APIRouter(prefix='/v1/soil', tags=['proxy.soil'])

@router.get("/fields/{field_id}/map")
async def soil_map(field_id: str, request: Request, tenant_id: str):
    rate_limit(request)
    return await get_json(f"{settings.SOIL_CORE_URL}/v1/soil/fields/{field_id}/map", params={"tenant_id":tenant_id})

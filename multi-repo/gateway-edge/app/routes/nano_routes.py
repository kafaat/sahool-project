from fastapi import APIRouter, Request
from ..core.ratelimit import rate_limit
from ..nanos.field_overview import build_field_overview
from ..nanos.timeline_compare import build_timeline_compare
from ..nanos.health_all import health_all
router=APIRouter(prefix="/v1/nano", tags=["nanos"])
@router.get("/health/all")
async def nano_health_all(request: Request):
    rate_limit(request); return await health_all()
@router.get("/fields/{field_id}/overview")
async def field_overview(field_id: str, request: Request, tenant_id: str):
    rate_limit(request); return await build_field_overview(field_id, tenant_id)
@router.get("/fields/{field_id}/timeline_compare")
async def timeline_compare(field_id: str, request: Request, tenant_id: str, from_date: str, to_date: str):
    rate_limit(request); return await build_timeline_compare(field_id, tenant_id, from_date, to_date)
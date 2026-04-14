from fastapi import APIRouter, Query, Header
from pydantic import BaseModel
from typing import Optional

from app.services.agent_service import build_field_advice, get_ndvi_analysis

router = APIRouter(prefix="/api/v1/agent", tags=["agent-ai"])


class AgentRequest(BaseModel):
    field_id: str
    message: str


@router.post("/field-advice")
async def field_advice(
    payload: AgentRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """Get AI advice for a field based on user message."""
    return await build_field_advice(x_tenant_id, payload.field_id, payload.message)


@router.get("/field/{field_id}/ndvi-analysis")
async def ndvi_analysis(
    field_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """Get AI-powered NDVI analysis for a field."""
    return await get_ndvi_analysis(x_tenant_id, field_id)

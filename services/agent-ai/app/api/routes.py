from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.agent_service import build_field_advice, get_ndvi_analysis

router = APIRouter(prefix="/api/v1/agent", tags=["agent-ai"])


class AgentRequest(BaseModel):
    tenant_id: int
    field_id: int
    message: str


@router.post("/field-advice")
async def field_advice(payload: AgentRequest):
    return await build_field_advice(payload.tenant_id, payload.field_id, payload.message)


@router.get("/field/{field_id}/ndvi-analysis")
async def ndvi_analysis(field_id: int, tenant_id: int = Query(...)):
    return await get_ndvi_analysis(tenant_id, field_id)

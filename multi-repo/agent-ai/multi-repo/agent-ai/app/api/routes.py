from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.agent_service import build_field_advice

router = APIRouter(prefix="/api/v1/agent", tags=["agent-ai"])

class AgentRequest(BaseModel):
    tenant_id: int
    field_id: int
    message: str

@router.post("/field-advice")
async def field_advice(payload: AgentRequest):
    return await build_field_advice(payload.tenant_id, payload.field_id, payload.message)
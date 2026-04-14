from fastapi import APIRouter, HTTPException
from .agent import generate_reply
router=APIRouter(prefix="/v1/agent", tags=["agent-ai"])
@router.post("/chat")
async def chat(payload: dict):
    if "tenant_id" not in payload or "message" not in payload:
        raise HTTPException(400,"tenant_id and message required")
    return await generate_reply(payload)
@router.get("/health")
def health(): return {"status":"ok","service":"agent-ai"}
"""
Agent-AI Main Application with Cost Tracking
Complete example integrating cost tracking system
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import cost tracking
from app.services.cost_tracker import get_cost_tracker, LLMCostTracker
from app.middleware.cost_middleware import CostTrackingMiddleware
from app.routers.cost_monitoring import router as cost_router

# Import agent services
from app.services.langchain_agent_refactored import get_agent, AgriculturalAgent
from app.services.retriever import get_retriever
from app.services.generator import get_generator

logger = logging.getLogger(__name__)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    field_data: Optional[dict] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


class AnalysisRequest(BaseModel):
    field_id: int
    field_data: dict
    query: Optional[str] = "قدم تحليل شامل وتوصيات للحقل"
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""

    logger.info("🚀 Starting Agent-AI service with cost tracking...")

    # Initialize cost tracker
    cost_tracker = get_cost_tracker(
        max_daily_cost=float(os.getenv("MAX_DAILY_LLM_COST", "100.0")),
        max_monthly_cost=float(os.getenv("MAX_MONTHLY_LLM_COST", "2000.0"))
    )

    logger.info(
        f"💰 Cost limits: Daily=${cost_tracker.max_daily_cost:.2f}, "
        f"Monthly=${cost_tracker.max_monthly_cost:.2f}"
    )

    # Initialize agent
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    agent = get_agent(llm_provider)

    logger.info(f"🤖 Agent initialized with provider: {llm_provider}")
    logger.info("✅ Agent-AI service started successfully")

    yield

    logger.info("👋 Shutting down Agent-AI service...")

    # Export final cost summary
    summary_json = cost_tracker.export_summary_json()
    logger.info(f"📊 Final cost summary:\n{summary_json}")


# Create app
app = FastAPI(
    title="Agent-AI with Cost Tracking",
    description="Agricultural AI Agent with comprehensive cost monitoring",
    version="3.2.4",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add cost tracking middleware
app.add_middleware(CostTrackingMiddleware)

# Include cost monitoring router
app.include_router(cost_router)


@app.get("/")
async def root():
    """Root endpoint"""
    cost_tracker = get_cost_tracker()
    return {
        "service": "Agent-AI with Cost Tracking",
        "version": "3.2.4",
        "status": "running",
        "cost_tracking": {
            "enabled": True,
            "daily_cost": f"${cost_tracker.daily_cost:.2f}",
            "daily_limit": f"${cost_tracker.max_daily_cost:.2f}",
            "monthly_cost": f"${cost_tracker.monthly_cost:.2f}",
            "monthly_limit": f"${cost_tracker.max_monthly_cost:.2f}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cost_tracker = get_cost_tracker()

    daily_percentage = (cost_tracker.daily_cost / cost_tracker.max_daily_cost) * 100

    return {
        "status": "healthy",
        "cost_status": "critical" if daily_percentage >= 90 else "ok",
        "daily_cost_percentage": f"{daily_percentage:.1f}%"
    }


@app.post("/agent/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat with agricultural agent (with cost tracking)

    Args:
        message: User message
        field_data: Optional field context
        user_id: Optional user ID
        tenant_id: Optional tenant ID

    Returns:
        Agent response with cost information
    """
    try:
        cost_tracker = get_cost_tracker()
        agent = get_agent()

        # Estimate cost before processing
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        estimated_cost = cost_tracker.estimate_cost_from_text(
            model=model,
            text=request.message,
            estimated_output_ratio=2.0
        )

        # Check limits (already done by middleware, but double-check)
        check_result = cost_tracker.check_limits(estimated_cost, request.tenant_id)
        if not check_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=check_result["message"]
            )

        # Process request
        result = await agent.chat(
            message=request.message,
            field_data=request.field_data
        )

        # Estimate actual tokens (rough approximation)
        # In production, use actual token counts from LLM response
        input_tokens = len(request.message) // 4
        output_tokens = len(result.get("response", "")) // 4

        # Record actual usage
        usage_record = cost_tracker.record_usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            endpoint="/agent/chat"
        )

        # Return response with cost info
        return {
            **result,
            "cost_info": {
                "estimated_cost": f"${estimated_cost:.4f}",
                "actual_cost": f"${usage_record.cost:.4f}",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "daily_total": f"${cost_tracker.daily_cost:.2f}",
                "daily_remaining": f"${cost_tracker.max_daily_cost - cost_tracker.daily_cost:.2f}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/analyze")
async def analyze_field_endpoint(request: AnalysisRequest):
    """
    Analyze field (with cost tracking)

    Args:
        field_id: Field ID
        field_data: Field data (soil, weather, NDVI, etc.)
        query: Analysis query
        user_id: Optional user ID
        tenant_id: Optional tenant ID

    Returns:
        Analysis with cost information
    """
    try:
        cost_tracker = get_cost_tracker()
        agent = get_agent()

        # Estimate cost
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        # Analysis typically generates more text
        estimated_cost = cost_tracker.estimate_cost_from_text(
            model=model,
            text=request.query + str(request.field_data),
            estimated_output_ratio=3.0  # Analysis generates more output
        )

        # Check limits
        check_result = cost_tracker.check_limits(estimated_cost, request.tenant_id)
        if not check_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=check_result["message"]
            )

        # Process analysis
        result = await agent.analyze_field(
            field_id=request.field_id,
            field_data=request.field_data,
            query=request.query
        )

        # Estimate tokens
        input_tokens = (len(request.query) + len(str(request.field_data))) // 4
        output_tokens = len(result.get("analysis", "")) // 4

        # Record usage
        usage_record = cost_tracker.record_usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            endpoint="/agent/analyze"
        )

        # Return with cost info
        return {
            **result,
            "cost_info": {
                "estimated_cost": f"${estimated_cost:.4f}",
                "actual_cost": f"${usage_record.cost:.4f}",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "daily_total": f"${cost_tracker.daily_cost:.2f}",
                "daily_remaining": f"${cost_tracker.max_daily_cost - cost_tracker.daily_cost:.2f}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_with_cost_tracking:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )

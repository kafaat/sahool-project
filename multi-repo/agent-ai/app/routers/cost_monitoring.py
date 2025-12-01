"""
Cost Monitoring API Endpoints
View and manage LLM cost tracking
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.cost_tracker import get_cost_tracker, CostSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/cost", tags=["Cost Monitoring"])


class CostStatus(BaseModel):
    """Current cost status"""
    daily_cost: float
    daily_limit: float
    daily_percentage: float
    daily_remaining: float
    monthly_cost: float
    monthly_limit: float
    monthly_percentage: float
    monthly_remaining: float
    status: str  # "ok", "warning", "critical"
    message: str


class UsageStats(BaseModel):
    """Usage statistics"""
    total_cost: float
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    by_model: dict
    by_provider: dict
    by_tenant: dict


@router.get("/status", response_model=CostStatus)
async def get_cost_status():
    """
    Get current cost status

    Returns:
        Current daily and monthly costs with limits
    """
    try:
        tracker = get_cost_tracker()

        daily_percentage = (tracker.daily_cost / tracker.max_daily_cost) * 100
        monthly_percentage = (tracker.monthly_cost / tracker.max_monthly_cost) * 100

        # Determine status
        if daily_percentage >= 90 or monthly_percentage >= 90:
            status = "critical"
            message = "🔴 مستوى التكلفة حرج! اقتربت من الحد الأقصى"
        elif daily_percentage >= 75 or monthly_percentage >= 75:
            status = "warning"
            message = "🟡 تحذير: التكلفة مرتفعة، راقب الاستخدام"
        else:
            status = "ok"
            message = "🟢 التكلفة ضمن الحدود الطبيعية"

        return CostStatus(
            daily_cost=tracker.daily_cost,
            daily_limit=tracker.max_daily_cost,
            daily_percentage=daily_percentage,
            daily_remaining=tracker.max_daily_cost - tracker.daily_cost,
            monthly_cost=tracker.monthly_cost,
            monthly_limit=tracker.max_monthly_cost,
            monthly_percentage=monthly_percentage,
            monthly_remaining=tracker.max_monthly_cost - tracker.monthly_cost,
            status=status,
            message=message
        )

    except Exception as e:
        logger.error(f"Error getting cost status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/daily", response_model=UsageStats)
async def get_daily_summary():
    """
    Get daily usage summary

    Returns:
        Usage statistics for today
    """
    try:
        tracker = get_cost_tracker()
        summary = tracker.get_daily_summary()

        return UsageStats(
            total_cost=summary.total_cost,
            total_requests=summary.total_requests,
            total_input_tokens=summary.total_input_tokens,
            total_output_tokens=summary.total_output_tokens,
            by_model=summary.by_model,
            by_provider=summary.by_provider,
            by_tenant=summary.by_tenant
        )

    except Exception as e:
        logger.error(f"Error getting daily summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/monthly", response_model=UsageStats)
async def get_monthly_summary():
    """
    Get monthly usage summary

    Returns:
        Usage statistics for current month
    """
    try:
        tracker = get_cost_tracker()
        summary = tracker.get_monthly_summary()

        return UsageStats(
            total_cost=summary.total_cost,
            total_requests=summary.total_requests,
            total_input_tokens=summary.total_input_tokens,
            total_output_tokens=summary.total_output_tokens,
            by_model=summary.by_model,
            by_provider=summary.by_provider,
            by_tenant=summary.by_tenant
        )

    except Exception as e:
        logger.error(f"Error getting monthly summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/custom")
async def get_custom_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID")
):
    """
    Get custom period summary

    Args:
        start_date: Start date (default: 30 days ago)
        end_date: End date (default: now)
        tenant_id: Optional tenant filter

    Returns:
        Usage statistics for specified period
    """
    try:
        tracker = get_cost_tracker()

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        summary = tracker.get_summary(
            start_date=start,
            end_date=end,
            tenant_id=tenant_id
        )

        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": (end - start).days
            },
            "tenant_id": tenant_id,
            "stats": {
                "total_cost": summary.total_cost,
                "total_requests": summary.total_requests,
                "total_input_tokens": summary.total_input_tokens,
                "total_output_tokens": summary.total_output_tokens,
                "by_model": summary.by_model,
                "by_provider": summary.by_provider,
                "by_tenant": summary.by_tenant
            }
        }

    except Exception as e:
        logger.error(f"Error getting custom summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_daily_json():
    """
    Export daily summary as JSON

    Returns:
        JSON export of daily usage
    """
    try:
        tracker = get_cost_tracker()
        return tracker.export_summary_json()

    except Exception as e:
        logger.error(f"Error exporting JSON: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/limits/update")
async def update_limits(
    daily_limit: Optional[float] = Query(None, description="New daily limit"),
    monthly_limit: Optional[float] = Query(None, description="New monthly limit")
):
    """
    Update cost limits (admin only)

    Args:
        daily_limit: New daily limit in USD
        monthly_limit: New monthly limit in USD

    Returns:
        Updated limits
    """
    try:
        tracker = get_cost_tracker()

        if daily_limit is not None:
            tracker.max_daily_cost = daily_limit
            logger.info(f"Daily limit updated to ${daily_limit:.2f}")

        if monthly_limit is not None:
            tracker.max_monthly_cost = monthly_limit
            logger.info(f"Monthly limit updated to ${monthly_limit:.2f}")

        return {
            "success": True,
            "daily_limit": tracker.max_daily_cost,
            "monthly_limit": tracker.max_monthly_cost
        }

    except Exception as e:
        logger.error(f"Error updating limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/daily")
async def reset_daily_cost():
    """
    Manually reset daily cost (admin only)

    Returns:
        Success status
    """
    try:
        tracker = get_cost_tracker()
        old_cost = tracker.daily_cost
        tracker.reset_daily_cost()

        logger.info(f"Daily cost manually reset from ${old_cost:.2f}")

        return {
            "success": True,
            "message": f"Daily cost reset from ${old_cost:.2f} to $0.00"
        }

    except Exception as e:
        logger.error(f"Error resetting daily cost: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimate")
async def estimate_cost(
    model: str = Query("gpt-3.5-turbo", description="Model name"),
    input_text: str = Query(..., description="Input text to estimate"),
    output_ratio: float = Query(1.5, description="Expected output/input ratio")
):
    """
    Estimate cost for a potential request

    Args:
        model: Model name
        input_text: Input text
        output_ratio: Expected output/input token ratio

    Returns:
        Estimated cost
    """
    try:
        tracker = get_cost_tracker()
        estimated_cost = tracker.estimate_cost_from_text(model, input_text, output_ratio)

        return {
            "model": model,
            "input_length": len(input_text),
            "estimated_input_tokens": len(input_text) // 4,
            "estimated_output_tokens": int((len(input_text) // 4) * output_ratio),
            "estimated_cost": estimated_cost,
            "formatted_cost": f"${estimated_cost:.4f}"
        }

    except Exception as e:
        logger.error(f"Error estimating cost: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

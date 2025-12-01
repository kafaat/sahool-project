"""
Cost Tracking Middleware for FastAPI
Intercepts requests to check and enforce cost limits
"""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.cost_tracker import get_cost_tracker, LLMCostTracker

logger = logging.getLogger(__name__)


class CostTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check cost limits before processing requests
    """

    def __init__(self, app, cost_tracker: LLMCostTracker = None):
        super().__init__(app)
        self.cost_tracker = cost_tracker or get_cost_tracker()

    async def dispatch(self, request: Request, call_next):
        """
        Intercept request and check cost limits for LLM endpoints
        """
        # Only check for LLM-using endpoints
        llm_endpoints = ["/agent/chat", "/agent/analyze", "/api/v2/agent/"]

        is_llm_endpoint = any(endpoint in str(request.url.path) for endpoint in llm_endpoints)

        if is_llm_endpoint and request.method == "POST":
            try:
                # Get request body to estimate cost
                body = await request.body()

                # Rough estimation based on body size
                # More accurate estimation will happen in the actual handler
                estimated_input_tokens = len(body) // 4  # 1 token ≈ 4 chars
                estimated_output_tokens = estimated_input_tokens * 2  # Conservative estimate

                # Use a default model for estimation (actual will be tracked later)
                estimated_cost = self.cost_tracker.estimate_cost(
                    model="gpt-3.5-turbo",
                    input_tokens=estimated_input_tokens,
                    output_tokens=estimated_output_tokens
                )

                # Check limits
                check_result = self.cost_tracker.check_limits(estimated_cost)

                if not check_result["allowed"]:
                    logger.warning(
                        f"Request blocked - {check_result['reason']}: "
                        f"{check_result['message']}"
                    )
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "cost_limit_exceeded",
                            "message": check_result["message"],
                            "details": {
                                "daily_cost": f"${self.cost_tracker.daily_cost:.2f}",
                                "daily_limit": f"${self.cost_tracker.max_daily_cost:.2f}",
                                "monthly_cost": f"${self.cost_tracker.monthly_cost:.2f}",
                                "monthly_limit": f"${self.cost_tracker.max_monthly_cost:.2f}",
                            }
                        }
                    )

                # Log warnings
                for warning in check_result.get("warnings", []):
                    logger.warning(f"Cost alert: {warning['message']}")

                # Store check result in request state for logging
                request.state.cost_check = check_result

            except Exception as e:
                logger.error(f"Error in cost tracking middleware: {e}", exc_info=True)
                # Don't block request on middleware errors
                pass

        # Process request
        response = await call_next(request)
        return response

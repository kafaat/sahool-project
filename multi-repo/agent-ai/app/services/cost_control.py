"""
LLM Cost Control Service
التحكم في تكلفة LLM لمنع الفواتير غير المتوقعة
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class LLMCostController:
    """
    Control and monitor LLM costs

    Features:
    - Track daily and monthly costs
    - Enforce cost limits
    - Estimate costs before API calls
    - Alert on threshold breaches
    - Per-tenant cost tracking
    """

    # Model pricing (per 1K tokens) - Updated 2024 prices
    MODEL_PRICING = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(
        self,
        max_daily_cost: float = None,
        max_monthly_cost: float = None,
        default_model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize cost controller

        Args:
            max_daily_cost: Maximum cost per day (default: from env or $100)
            max_monthly_cost: Maximum cost per month (default: from env or $2000)
            default_model: Default LLM model to use
        """

        self.max_daily_cost = max_daily_cost or float(
            os.getenv("MAX_DAILY_LLM_COST", "100.0")
        )

        self.max_monthly_cost = max_monthly_cost or float(
            os.getenv("MAX_MONTHLY_LLM_COST", "2000.0")
        )

        self.default_model = default_model

        # Track costs
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self.cost_by_tenant: Dict[str, float] = {}

        # Track dates for reset
        self.last_daily_reset = datetime.utcnow().date()
        self.last_monthly_reset = datetime.utcnow().replace(day=1).date()

        logger.info(
            f"💰 LLM Cost Controller initialized: "
            f"Daily limit: ${self.max_daily_cost}, "
            f"Monthly limit: ${self.max_monthly_cost}"
        )

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a request

        Args:
            model: LLM model name
            input_tokens: Number of input tokens
            output_tokens: Estimated output tokens

        Returns:
            Estimated cost in USD
        """

        if model not in self.MODEL_PRICING:
            logger.warning(f"Unknown model: {model}, using default pricing")
            model = self.default_model

        pricing = self.MODEL_PRICING[model]

        input_cost = (input_tokens / 1000.0) * pricing["input"]
        output_cost = (output_tokens / 1000.0) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def check_cost_limits(
        self,
        estimated_cost: float,
        tenant_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Check if request is allowed based on cost limits

        Args:
            estimated_cost: Estimated cost of the request
            tenant_id: Optional tenant ID for per-tenant tracking

        Returns:
            {
                "allowed": bool,
                "reason": str (if not allowed),
                "daily_usage": float,
                "monthly_usage": float,
                "daily_remaining": float,
                "monthly_remaining": float
            }
        """

        # Reset counters if needed
        self._reset_if_needed()

        # Check daily limit
        new_daily_cost = self.daily_cost + estimated_cost

        if new_daily_cost > self.max_daily_cost:
            logger.warning(
                f"⚠️  Daily cost limit reached: "
                f"${new_daily_cost:.2f} > ${self.max_daily_cost:.2f}"
            )

            return {
                "allowed": False,
                "reason": "daily_limit_exceeded",
                "message": f"Daily LLM cost limit of ${self.max_daily_cost:.2f} exceeded",
                "daily_usage": self.daily_cost,
                "daily_limit": self.max_daily_cost,
            }

        # Check monthly limit
        new_monthly_cost = self.monthly_cost + estimated_cost

        if new_monthly_cost > self.max_monthly_cost:
            logger.warning(
                f"⚠️  Monthly cost limit reached: "
                f"${new_monthly_cost:.2f} > ${self.max_monthly_cost:.2f}"
            )

            return {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "message": f"Monthly LLM cost limit of ${self.max_monthly_cost:.2f} exceeded",
                "monthly_usage": self.monthly_cost,
                "monthly_limit": self.max_monthly_cost,
            }

        # Request is allowed
        return {
            "allowed": True,
            "daily_usage": self.daily_cost,
            "monthly_usage": self.monthly_cost,
            "daily_remaining": self.max_daily_cost - self.daily_cost,
            "monthly_remaining": self.max_monthly_cost - self.monthly_cost,
            "estimated_cost": estimated_cost,
        }

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tenant_id: Optional[str] = None
    ) -> float:
        """
        Record actual usage and update costs

        Args:
            model: LLM model used
            input_tokens: Actual input tokens
            output_tokens: Actual output tokens
            tenant_id: Optional tenant ID

        Returns:
            Actual cost of the request
        """

        cost = self.estimate_cost(model, input_tokens, output_tokens)

        self.daily_cost += cost
        self.monthly_cost += cost

        # Track per-tenant costs
        if tenant_id:
            self.cost_by_tenant[tenant_id] = (
                self.cost_by_tenant.get(tenant_id, 0.0) + cost
            )

        logger.info(
            f"💰 Usage recorded: ${cost:.4f} | "
            f"Daily: ${self.daily_cost:.2f} | "
            f"Monthly: ${self.monthly_cost:.2f}"
            + (f" | Tenant: {tenant_id}" if tenant_id else "")
        )

        return cost

    def get_status(self) -> Dict[str, any]:
        """
        Get current cost status

        Returns:
            {
                "daily_cost": float,
                "monthly_cost": float,
                "daily_limit": float,
                "monthly_limit": float,
                "daily_remaining": float,
                "monthly_remaining": float,
                "daily_usage_percent": float,
                "monthly_usage_percent": float,
                "alert_level": str
            }
        """

        self._reset_if_needed()

        daily_percent = (self.daily_cost / self.max_daily_cost) * 100
        monthly_percent = (self.monthly_cost / self.max_monthly_cost) * 100

        # Determine alert level
        max_percent = max(daily_percent, monthly_percent)

        if max_percent >= 90:
            alert_level = "critical"
        elif max_percent >= 75:
            alert_level = "warning"
        elif max_percent >= 50:
            alert_level = "caution"
        else:
            alert_level = "ok"

        return {
            "daily_cost": round(self.daily_cost, 2),
            "monthly_cost": round(self.monthly_cost, 2),
            "daily_limit": self.max_daily_cost,
            "monthly_limit": self.max_monthly_cost,
            "daily_remaining": round(self.max_daily_cost - self.daily_cost, 2),
            "monthly_remaining": round(self.max_monthly_cost - self.monthly_cost, 2),
            "daily_usage_percent": round(daily_percent, 1),
            "monthly_usage_percent": round(monthly_percent, 1),
            "alert_level": alert_level,
            "tenant_costs": {
                tenant: round(cost, 2)
                for tenant, cost in self.cost_by_tenant.items()
            }
        }

    def _reset_if_needed(self):
        """Reset counters if a new day/month has started"""

        now = datetime.utcnow()
        today = now.date()

        # Reset daily counter
        if today > self.last_daily_reset:
            logger.info(
                f"📅 Resetting daily cost counter: ${self.daily_cost:.2f}"
            )
            self.daily_cost = 0.0
            self.last_daily_reset = today

        # Reset monthly counter
        first_of_month = now.replace(day=1).date()

        if first_of_month > self.last_monthly_reset:
            logger.info(
                f"📅 Resetting monthly cost counter: ${self.monthly_cost:.2f}"
            )
            self.monthly_cost = 0.0
            self.cost_by_tenant.clear()
            self.last_monthly_reset = first_of_month


# Global instance
cost_controller = LLMCostController()


def enforce_cost_limit(
    model: str,
    input_tokens: int,
    output_tokens: int,
    tenant_id: Optional[str] = None
):
    """
    Decorator/dependency to enforce cost limits

    Usage:
        @app.post("/chat")
        async def chat(message: str, tenant_id: str):
            # Estimate tokens
            input_tokens = len(message.split())
            estimated_output = 500

            # Check limits
            check = cost_controller.check_cost_limits(
                cost_controller.estimate_cost("gpt-3.5-turbo", input_tokens, estimated_output),
                tenant_id
            )

            if not check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail=check["message"]
                )

            # Make LLM call
            response = await llm.generate(message)

            # Record actual usage
            cost_controller.record_usage(
                "gpt-3.5-turbo",
                input_tokens,
                len(response.split()),
                tenant_id
            )

            return {"response": response}
    """

    estimated_cost = cost_controller.estimate_cost(
        model, input_tokens, output_tokens
    )

    check = cost_controller.check_cost_limits(estimated_cost, tenant_id)

    if not check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=check["message"]
        )

    return check

"""
LLM Cost Tracking System
Prevents unexpected high costs by monitoring and limiting LLM usage
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    FALLBACK = "fallback"


class AlertLevel(str, Enum):
    """Cost alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ModelPricing:
    """Pricing information for a specific model"""
    input_cost_per_1k: float  # Cost per 1000 input tokens
    output_cost_per_1k: float  # Cost per 1000 output tokens
    provider: LLMProvider


# Pricing as of December 2024 (update regularly!)
MODEL_PRICING = {
    # OpenAI Models
    "gpt-4-turbo-preview": ModelPricing(0.01, 0.03, LLMProvider.OPENAI),
    "gpt-4": ModelPricing(0.03, 0.06, LLMProvider.OPENAI),
    "gpt-4-32k": ModelPricing(0.06, 0.12, LLMProvider.OPENAI),
    "gpt-3.5-turbo": ModelPricing(0.0015, 0.002, LLMProvider.OPENAI),
    "gpt-3.5-turbo-16k": ModelPricing(0.003, 0.004, LLMProvider.OPENAI),

    # Anthropic Claude Models
    "claude-3-opus-20240229": ModelPricing(0.015, 0.075, LLMProvider.ANTHROPIC),
    "claude-3-sonnet-20240229": ModelPricing(0.003, 0.015, LLMProvider.ANTHROPIC),
    "claude-3-haiku-20240307": ModelPricing(0.00025, 0.00125, LLMProvider.ANTHROPIC),
    "claude-2.1": ModelPricing(0.008, 0.024, LLMProvider.ANTHROPIC),

    # Fallback (free)
    "fallback": ModelPricing(0.0, 0.0, LLMProvider.FALLBACK),
}


@dataclass
class UsageRecord:
    """Record of a single LLM usage"""
    timestamp: datetime
    model: str
    provider: LLMProvider
    input_tokens: int
    output_tokens: int
    cost: float
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    endpoint: Optional[str] = None


@dataclass
class CostSummary:
    """Summary of costs for a time period"""
    total_cost: float
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    by_model: Dict[str, float] = field(default_factory=dict)
    by_provider: Dict[str, float] = field(default_factory=dict)
    by_tenant: Dict[str, float] = field(default_factory=dict)


class LLMCostTracker:
    """
    Tracks and limits LLM usage costs

    Features:
    - Daily and monthly cost limits
    - Per-tenant cost tracking
    - Cost estimation before requests
    - Alert notifications at thresholds
    - Usage history and analytics
    """

    def __init__(
        self,
        max_daily_cost: Optional[float] = None,
        max_monthly_cost: Optional[float] = None,
        alert_thresholds: Optional[List[float]] = None,
        redis_client = None
    ):
        """
        Initialize cost tracker

        Args:
            max_daily_cost: Maximum daily cost in USD (default from env or $100)
            max_monthly_cost: Maximum monthly cost in USD (default from env or $2000)
            alert_thresholds: Alert at these percentages [50, 75, 90]
            redis_client: Optional Redis client for persistence
        """
        self.max_daily_cost = max_daily_cost or float(
            os.getenv("MAX_DAILY_LLM_COST", "100.0")
        )
        self.max_monthly_cost = max_monthly_cost or float(
            os.getenv("MAX_MONTHLY_LLM_COST", "2000.0")
        )
        self.alert_thresholds = alert_thresholds or [50.0, 75.0, 90.0]
        self.redis_client = redis_client

        # In-memory tracking (for current session)
        self.usage_history: List[UsageRecord] = []
        self.daily_cost: float = 0.0
        self.monthly_cost: float = 0.0
        self.last_reset_date: datetime = datetime.now()
        self.alerts_sent: Dict[float, bool] = {t: False for t in self.alert_thresholds}

        # Load from Redis if available
        if self.redis_client:
            self._load_from_redis()

        logger.info(
            f"Cost Tracker initialized - "
            f"Daily limit: ${self.max_daily_cost:.2f}, "
            f"Monthly limit: ${self.max_monthly_cost:.2f}"
        )

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0
    ) -> float:
        """
        Estimate cost for a request

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (0 if estimating before request)

        Returns:
            Estimated cost in USD
        """
        if model not in MODEL_PRICING:
            logger.warning(f"Unknown model: {model}, using gpt-3.5-turbo pricing")
            model = "gpt-3.5-turbo"

        pricing = MODEL_PRICING[model]
        input_cost = (input_tokens / 1000.0) * pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000.0) * pricing.output_cost_per_1k

        return input_cost + output_cost

    def estimate_cost_from_text(
        self,
        model: str,
        text: str,
        estimated_output_ratio: float = 1.5
    ) -> float:
        """
        Estimate cost from text (before tokenization)

        Args:
            model: Model name
            text: Input text
            estimated_output_ratio: Estimated output/input token ratio

        Returns:
            Estimated cost in USD
        """
        # Rough estimation: 1 token ≈ 4 characters
        estimated_input_tokens = len(text) // 4
        estimated_output_tokens = int(estimated_input_tokens * estimated_output_ratio)

        return self.estimate_cost(model, estimated_input_tokens, estimated_output_tokens)

    def check_limits(
        self,
        estimated_cost: float,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request would exceed limits

        Args:
            estimated_cost: Estimated cost of the request
            tenant_id: Optional tenant ID for per-tenant limits

        Returns:
            Dict with allowed status and details
        """
        # Reset counters if new day/month
        self._check_reset()

        result = {
            "allowed": True,
            "estimated_cost": estimated_cost,
            "daily_cost_after": self.daily_cost + estimated_cost,
            "monthly_cost_after": self.monthly_cost + estimated_cost,
            "daily_limit": self.max_daily_cost,
            "monthly_limit": self.max_monthly_cost,
            "daily_remaining": self.max_daily_cost - self.daily_cost,
            "monthly_remaining": self.max_monthly_cost - self.monthly_cost,
            "warnings": []
        }

        # Check daily limit
        if self.daily_cost + estimated_cost > self.max_daily_cost:
            result["allowed"] = False
            result["reason"] = "daily_limit_exceeded"
            result["message"] = (
                f"🔴 Daily LLM cost limit reached: "
                f"${self.daily_cost:.2f}/${self.max_daily_cost:.2f}. "
                f"Limit will reset tomorrow."
            )
            return result

        # Check monthly limit
        if self.monthly_cost + estimated_cost > self.max_monthly_cost:
            result["allowed"] = False
            result["reason"] = "monthly_limit_exceeded"
            result["message"] = (
                f"🔴 Monthly LLM cost limit reached: "
                f"${self.monthly_cost:.2f}/${self.max_monthly_cost:.2f}. "
                f"Limit will reset next month."
            )
            return result

        # Check alert thresholds
        daily_percentage = (self.daily_cost / self.max_daily_cost) * 100
        for threshold in self.alert_thresholds:
            if daily_percentage >= threshold and not self.alerts_sent[threshold]:
                result["warnings"].append({
                    "level": self._get_alert_level(threshold),
                    "message": (
                        f"⚠️ Daily LLM cost at {daily_percentage:.1f}% "
                        f"(${self.daily_cost:.2f}/${self.max_daily_cost:.2f})"
                    ),
                    "threshold": threshold
                })
                self.alerts_sent[threshold] = True

        return result

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> UsageRecord:
        """
        Record actual LLM usage

        Args:
            model: Model used
            input_tokens: Actual input tokens
            output_tokens: Actual output tokens
            user_id: Optional user ID
            tenant_id: Optional tenant ID
            endpoint: Optional endpoint name

        Returns:
            UsageRecord with cost information
        """
        cost = self.estimate_cost(model, input_tokens, output_tokens)

        provider = MODEL_PRICING.get(model, MODEL_PRICING["gpt-3.5-turbo"]).provider

        record = UsageRecord(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint=endpoint
        )

        # Update counters
        self.daily_cost += cost
        self.monthly_cost += cost
        self.usage_history.append(record)

        # Persist to Redis if available
        if self.redis_client:
            self._save_to_redis(record)

        logger.info(
            f"Usage recorded - Model: {model}, "
            f"Tokens: {input_tokens}+{output_tokens}, "
            f"Cost: ${cost:.4f}, "
            f"Daily total: ${self.daily_cost:.2f}"
        )

        return record

    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None
    ) -> CostSummary:
        """
        Get cost summary for a period

        Args:
            start_date: Start date (default: today)
            end_date: End date (default: now)
            tenant_id: Filter by tenant

        Returns:
            CostSummary
        """
        start = start_date or datetime.now().replace(hour=0, minute=0, second=0)
        end = end_date or datetime.now()

        # Filter records
        records = [
            r for r in self.usage_history
            if start <= r.timestamp <= end
            and (tenant_id is None or r.tenant_id == tenant_id)
        ]

        if not records:
            return CostSummary(0.0, 0, 0, 0)

        summary = CostSummary(
            total_cost=sum(r.cost for r in records),
            total_requests=len(records),
            total_input_tokens=sum(r.input_tokens for r in records),
            total_output_tokens=sum(r.output_tokens for r in records)
        )

        # Breakdown by model
        for record in records:
            summary.by_model[record.model] = summary.by_model.get(record.model, 0.0) + record.cost
            summary.by_provider[record.provider] = summary.by_provider.get(record.provider, 0.0) + record.cost
            if record.tenant_id:
                summary.by_tenant[record.tenant_id] = summary.by_tenant.get(record.tenant_id, 0.0) + record.cost

        return summary

    def get_daily_summary(self) -> CostSummary:
        """Get summary for today"""
        return self.get_summary()

    def get_monthly_summary(self) -> CostSummary:
        """Get summary for current month"""
        start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        return self.get_summary(start_date=start)

    def reset_daily_cost(self):
        """Reset daily cost counter (called automatically at midnight)"""
        logger.info(f"Resetting daily cost from ${self.daily_cost:.2f} to $0.00")
        self.daily_cost = 0.0
        self.alerts_sent = {t: False for t in self.alert_thresholds}
        self.last_reset_date = datetime.now()

    def reset_monthly_cost(self):
        """Reset monthly cost counter (called automatically on 1st of month)"""
        logger.info(f"Resetting monthly cost from ${self.monthly_cost:.2f} to $0.00")
        self.monthly_cost = 0.0

    def _check_reset(self):
        """Check if counters need to be reset"""
        now = datetime.now()

        # Check daily reset
        if now.date() > self.last_reset_date.date():
            self.reset_daily_cost()

        # Check monthly reset
        if now.month != self.last_reset_date.month or now.year != self.last_reset_date.year:
            self.reset_monthly_cost()

    def _get_alert_level(self, threshold: float) -> AlertLevel:
        """Get alert level based on threshold"""
        if threshold >= 90:
            return AlertLevel.CRITICAL
        elif threshold >= 75:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO

    def _load_from_redis(self):
        """Load cost data from Redis"""
        try:
            if not self.redis_client:
                return

            # Load daily cost
            daily_key = f"llm_cost:daily:{datetime.now().strftime('%Y-%m-%d')}"
            daily_cost = self.redis_client.get(daily_key)
            if daily_cost:
                self.daily_cost = float(daily_cost)

            # Load monthly cost
            monthly_key = f"llm_cost:monthly:{datetime.now().strftime('%Y-%m')}"
            monthly_cost = self.redis_client.get(monthly_key)
            if monthly_cost:
                self.monthly_cost = float(monthly_cost)

            logger.info(
                f"Loaded from Redis - Daily: ${self.daily_cost:.2f}, "
                f"Monthly: ${self.monthly_cost:.2f}"
            )

        except Exception as e:
            logger.error(f"Error loading from Redis: {e}")

    def _save_to_redis(self, record: UsageRecord):
        """Save usage record to Redis"""
        try:
            if not self.redis_client:
                return

            # Update daily cost
            daily_key = f"llm_cost:daily:{record.timestamp.strftime('%Y-%m-%d')}"
            self.redis_client.incrbyfloat(daily_key, record.cost)
            self.redis_client.expire(daily_key, 86400 * 7)  # Keep for 7 days

            # Update monthly cost
            monthly_key = f"llm_cost:monthly:{record.timestamp.strftime('%Y-%m')}"
            self.redis_client.incrbyfloat(monthly_key, record.cost)
            self.redis_client.expire(monthly_key, 86400 * 90)  # Keep for 90 days

            # Store record
            record_key = f"llm_usage:{record.timestamp.isoformat()}"
            record_data = {
                "model": record.model,
                "provider": record.provider,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "cost": record.cost,
                "user_id": record.user_id or "",
                "tenant_id": record.tenant_id or "",
                "endpoint": record.endpoint or ""
            }
            self.redis_client.hmset(record_key, record_data)
            self.redis_client.expire(record_key, 86400 * 30)  # Keep for 30 days

        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")

    def export_summary_json(self) -> str:
        """Export daily summary as JSON"""
        summary = self.get_daily_summary()
        return json.dumps({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_cost": summary.total_cost,
            "total_requests": summary.total_requests,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "by_model": summary.by_model,
            "by_provider": summary.by_provider,
            "by_tenant": summary.by_tenant,
            "daily_limit": self.max_daily_cost,
            "monthly_limit": self.max_monthly_cost,
            "daily_cost": self.daily_cost,
            "monthly_cost": self.monthly_cost
        }, indent=2)


# Global instance
_cost_tracker: Optional[LLMCostTracker] = None


def get_cost_tracker(
    max_daily_cost: Optional[float] = None,
    max_monthly_cost: Optional[float] = None,
    redis_client = None
) -> LLMCostTracker:
    """Get or create global cost tracker instance"""
    global _cost_tracker

    if _cost_tracker is None:
        _cost_tracker = LLMCostTracker(
            max_daily_cost=max_daily_cost,
            max_monthly_cost=max_monthly_cost,
            redis_client=redis_client
        )

    return _cost_tracker


def reset_cost_tracker():
    """Reset global cost tracker (useful for testing)"""
    global _cost_tracker
    _cost_tracker = None

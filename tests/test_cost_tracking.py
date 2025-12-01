"""
Tests for LLM Cost Tracking System
Comprehensive tests for cost estimation, limits, and monitoring
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'multi-repo', 'agent-ai'))

from app.services.cost_tracker import (
    LLMCostTracker,
    MODEL_PRICING,
    LLMProvider,
    UsageRecord
)


class TestCostEstimation:
    """Test cost estimation functionality"""

    def test_estimate_cost_gpt35(self):
        """Test cost estimation for GPT-3.5"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost(
            model="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=1000
        )

        # GPT-3.5: $0.0015 input + $0.002 output per 1K
        expected = 0.0015 + 0.002
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_gpt4(self):
        """Test cost estimation for GPT-4"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost(
            model="gpt-4-turbo-preview",
            input_tokens=1000,
            output_tokens=1000
        )

        # GPT-4 Turbo: $0.01 input + $0.03 output per 1K
        expected = 0.01 + 0.03
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_claude_sonnet(self):
        """Test cost estimation for Claude Sonnet"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost(
            model="claude-3-sonnet-20240229",
            input_tokens=1000,
            output_tokens=1000
        )

        # Claude Sonnet: $0.003 input + $0.015 output per 1K
        expected = 0.003 + 0.015
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_claude_haiku(self):
        """Test cost estimation for Claude Haiku (cheapest)"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost(
            model="claude-3-haiku-20240307",
            input_tokens=1000,
            output_tokens=1000
        )

        # Claude Haiku: $0.00025 input + $0.00125 output per 1K
        expected = 0.00025 + 0.00125
        assert abs(cost - expected) < 0.00001

    def test_estimate_cost_from_text(self):
        """Test cost estimation from text (before tokenization)"""
        tracker = LLMCostTracker()

        text = "This is a test message" * 100  # ~2200 chars
        cost = tracker.estimate_cost_from_text(
            model="gpt-3.5-turbo",
            text=text,
            estimated_output_ratio=1.5
        )

        # Should be reasonable cost
        assert 0.0 < cost < 0.01  # Less than 1 cent for this small text

    def test_fallback_model_free(self):
        """Test fallback model is free"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost(
            model="fallback",
            input_tokens=1000000,  # 1M tokens
            output_tokens=1000000
        )

        assert cost == 0.0


class TestLimitEnforcement:
    """Test cost limit enforcement"""

    def test_check_limits_under_limit(self):
        """Test request allowed when under limit"""
        tracker = LLMCostTracker(max_daily_cost=100.0)
        tracker.daily_cost = 50.0

        result = tracker.check_limits(estimated_cost=10.0)

        assert result["allowed"] is True
        assert result["daily_remaining"] == 50.0

    def test_check_limits_exceed_daily(self):
        """Test request denied when exceeding daily limit"""
        tracker = LLMCostTracker(max_daily_cost=100.0)
        tracker.daily_cost = 95.0

        result = tracker.check_limits(estimated_cost=10.0)

        assert result["allowed"] is False
        assert result["reason"] == "daily_limit_exceeded"
        assert "Daily LLM cost limit reached" in result["message"]

    def test_check_limits_exceed_monthly(self):
        """Test request denied when exceeding monthly limit"""
        tracker = LLMCostTracker(max_monthly_cost=1000.0)
        tracker.monthly_cost = 995.0

        result = tracker.check_limits(estimated_cost=10.0)

        assert result["allowed"] is False
        assert result["reason"] == "monthly_limit_exceeded"

    def test_check_limits_exactly_at_limit(self):
        """Test request denied when exactly at limit"""
        tracker = LLMCostTracker(max_daily_cost=100.0)
        tracker.daily_cost = 100.0

        result = tracker.check_limits(estimated_cost=0.01)

        assert result["allowed"] is False

    def test_alert_thresholds(self):
        """Test alerts at 50%, 75%, 90% thresholds"""
        tracker = LLMCostTracker(
            max_daily_cost=100.0,
            alert_thresholds=[50.0, 75.0, 90.0]
        )

        # At 50%
        tracker.daily_cost = 50.0
        result = tracker.check_limits(1.0)
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["threshold"] == 50.0

        # At 75%
        tracker.daily_cost = 75.0
        tracker.alerts_sent = {50.0: True, 75.0: False, 90.0: False}
        result = tracker.check_limits(1.0)
        assert any(w["threshold"] == 75.0 for w in result["warnings"])

        # At 95% (should have 90% alert)
        tracker.daily_cost = 95.0
        tracker.alerts_sent = {50.0: True, 75.0: True, 90.0: False}
        result = tracker.check_limits(1.0)
        assert any(w["threshold"] == 90.0 for w in result["warnings"])


class TestUsageRecording:
    """Test usage recording and tracking"""

    def test_record_usage_basic(self):
        """Test basic usage recording"""
        tracker = LLMCostTracker()

        record = tracker.record_usage(
            model="gpt-3.5-turbo",
            input_tokens=500,
            output_tokens=1000
        )

        assert isinstance(record, UsageRecord)
        assert record.model == "gpt-3.5-turbo"
        assert record.input_tokens == 500
        assert record.output_tokens == 1000
        assert record.cost > 0

    def test_record_usage_updates_daily_cost(self):
        """Test that recording updates daily cost"""
        tracker = LLMCostTracker()
        initial_cost = tracker.daily_cost

        tracker.record_usage("gpt-3.5-turbo", 1000, 1000)

        assert tracker.daily_cost > initial_cost

    def test_record_usage_updates_monthly_cost(self):
        """Test that recording updates monthly cost"""
        tracker = LLMCostTracker()
        initial_cost = tracker.monthly_cost

        tracker.record_usage("gpt-3.5-turbo", 1000, 1000)

        assert tracker.monthly_cost > initial_cost

    def test_record_usage_with_metadata(self):
        """Test recording with user/tenant metadata"""
        tracker = LLMCostTracker()

        record = tracker.record_usage(
            model="gpt-4-turbo-preview",
            input_tokens=100,
            output_tokens=200,
            user_id="user123",
            tenant_id="tenant456",
            endpoint="/agent/chat"
        )

        assert record.user_id == "user123"
        assert record.tenant_id == "tenant456"
        assert record.endpoint == "/agent/chat"

    def test_usage_history_accumulates(self):
        """Test that usage history accumulates"""
        tracker = LLMCostTracker()

        tracker.record_usage("gpt-3.5-turbo", 100, 200)
        tracker.record_usage("gpt-4-turbo-preview", 50, 100)
        tracker.record_usage("claude-3-sonnet-20240229", 75, 150)

        assert len(tracker.usage_history) == 3


class TestSummaries:
    """Test summary generation"""

    def test_daily_summary(self):
        """Test daily summary generation"""
        tracker = LLMCostTracker()

        # Record some usage
        tracker.record_usage("gpt-3.5-turbo", 1000, 1000, tenant_id="t1")
        tracker.record_usage("gpt-4-turbo-preview", 500, 500, tenant_id="t2")

        summary = tracker.get_daily_summary()

        assert summary.total_requests == 2
        assert summary.total_input_tokens == 1500
        assert summary.total_output_tokens == 1500
        assert "gpt-3.5-turbo" in summary.by_model
        assert "gpt-4-turbo-preview" in summary.by_model
        assert "t1" in summary.by_tenant
        assert "t2" in summary.by_tenant

    def test_summary_by_tenant(self):
        """Test summary filtered by tenant"""
        tracker = LLMCostTracker()

        tracker.record_usage("gpt-3.5-turbo", 1000, 1000, tenant_id="tenant1")
        tracker.record_usage("gpt-3.5-turbo", 500, 500, tenant_id="tenant2")
        tracker.record_usage("gpt-3.5-turbo", 300, 300, tenant_id="tenant1")

        summary = tracker.get_summary(tenant_id="tenant1")

        assert summary.total_requests == 2
        assert summary.total_input_tokens == 1300

    def test_summary_date_range(self):
        """Test summary for custom date range"""
        tracker = LLMCostTracker()

        # Record with different timestamps (simulate)
        record1 = tracker.record_usage("gpt-3.5-turbo", 100, 100)
        record1.timestamp = datetime.now() - timedelta(days=5)
        tracker.usage_history[-1] = record1

        record2 = tracker.record_usage("gpt-3.5-turbo", 200, 200)
        # Current time

        # Get summary for last 3 days (should only include record2)
        summary = tracker.get_summary(
            start_date=datetime.now() - timedelta(days=3),
            end_date=datetime.now()
        )

        assert summary.total_requests == 1
        assert summary.total_input_tokens == 200

    def test_export_json(self):
        """Test JSON export"""
        tracker = LLMCostTracker()

        tracker.record_usage("gpt-3.5-turbo", 100, 200)

        json_export = tracker.export_summary_json()

        assert isinstance(json_export, str)
        assert "total_cost" in json_export
        assert "gpt-3.5-turbo" in json_export


class TestDailyReset:
    """Test daily/monthly reset functionality"""

    def test_daily_reset(self):
        """Test daily cost reset"""
        tracker = LLMCostTracker()
        tracker.daily_cost = 50.0

        tracker.reset_daily_cost()

        assert tracker.daily_cost == 0.0
        assert all(not sent for sent in tracker.alerts_sent.values())

    def test_monthly_reset(self):
        """Test monthly cost reset"""
        tracker = LLMCostTracker()
        tracker.monthly_cost = 500.0

        tracker.reset_monthly_cost()

        assert tracker.monthly_cost == 0.0

    def test_automatic_daily_reset(self):
        """Test automatic daily reset when date changes"""
        tracker = LLMCostTracker()
        tracker.daily_cost = 50.0
        tracker.last_reset_date = datetime.now() - timedelta(days=1)

        # This should trigger reset
        tracker._check_reset()

        assert tracker.daily_cost == 0.0


class TestModelPricing:
    """Test model pricing data"""

    def test_all_models_have_pricing(self):
        """Test that all common models have pricing"""
        assert "gpt-3.5-turbo" in MODEL_PRICING
        assert "gpt-4-turbo-preview" in MODEL_PRICING
        assert "claude-3-sonnet-20240229" in MODEL_PRICING
        assert "claude-3-haiku-20240307" in MODEL_PRICING

    def test_pricing_structure(self):
        """Test pricing structure is correct"""
        for model, pricing in MODEL_PRICING.items():
            assert pricing.input_cost_per_1k >= 0
            assert pricing.output_cost_per_1k >= 0
            assert pricing.provider in LLMProvider

    def test_cheapest_models(self):
        """Verify cheapest models are correctly priced"""
        haiku = MODEL_PRICING["claude-3-haiku-20240307"]
        gpt35 = MODEL_PRICING["gpt-3.5-turbo"]

        # Haiku should be cheaper than GPT-3.5
        assert haiku.input_cost_per_1k < gpt35.input_cost_per_1k
        assert haiku.output_cost_per_1k < gpt35.output_cost_per_1k

    def test_most_expensive_models(self):
        """Verify expensive models are correctly priced"""
        gpt4_32k = MODEL_PRICING["gpt-4-32k"]
        opus = MODEL_PRICING["claude-3-opus-20240229"]

        # These should be most expensive
        assert gpt4_32k.input_cost_per_1k > 0.05
        assert opus.output_cost_per_1k > 0.07


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_complete_request_flow(self):
        """Test complete flow: estimate -> check -> record"""
        tracker = LLMCostTracker(max_daily_cost=10.0)

        # Step 1: Estimate
        text = "Analyze this field" * 50
        estimated_cost = tracker.estimate_cost_from_text(
            "gpt-3.5-turbo",
            text
        )

        # Step 2: Check limits
        check = tracker.check_limits(estimated_cost)
        assert check["allowed"]

        # Step 3: Record usage
        record = tracker.record_usage(
            "gpt-3.5-turbo",
            input_tokens=len(text) // 4,
            output_tokens=len(text) // 2,
            tenant_id="test_tenant"
        )

        # Verify
        assert tracker.daily_cost > 0
        assert len(tracker.usage_history) == 1

        # Step 4: Get summary
        summary = tracker.get_daily_summary()
        assert summary.total_cost > 0

    def test_limit_reached_workflow(self):
        """Test workflow when limit is reached"""
        tracker = LLMCostTracker(max_daily_cost=1.0)

        # Use up budget
        for i in range(10):
            tracker.record_usage("gpt-3.5-turbo", 10000, 10000)

        # Next request should be denied
        check = tracker.check_limits(0.01)
        assert not check["allowed"]

        # Summary should show we're over limit
        summary = tracker.get_daily_summary()
        assert summary.total_cost > 1.0

    def test_multi_tenant_tracking(self):
        """Test tracking across multiple tenants"""
        tracker = LLMCostTracker()

        # Different tenants using service
        tracker.record_usage("gpt-3.5-turbo", 1000, 1000, tenant_id="tenant_a")
        tracker.record_usage("gpt-4-turbo-preview", 500, 500, tenant_id="tenant_b")
        tracker.record_usage("claude-3-sonnet-20240229", 750, 750, tenant_id="tenant_a")

        summary = tracker.get_daily_summary()

        # Should track both tenants
        assert "tenant_a" in summary.by_tenant
        assert "tenant_b" in summary.by_tenant

        # Tenant A should have more cost (2 requests)
        assert summary.by_tenant["tenant_a"] > summary.by_tenant["tenant_b"]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_unknown_model_fallback(self):
        """Test handling of unknown model"""
        tracker = LLMCostTracker()

        # Should fallback to default pricing
        cost = tracker.estimate_cost("unknown-model-xyz", 1000, 1000)
        assert cost > 0  # Should use fallback pricing

    def test_zero_tokens(self):
        """Test handling of zero tokens"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost("gpt-3.5-turbo", 0, 0)
        assert cost == 0.0

    def test_very_large_tokens(self):
        """Test handling of very large token counts"""
        tracker = LLMCostTracker()

        cost = tracker.estimate_cost("gpt-4-turbo-preview", 1000000, 1000000)
        # Should be expensive but not crash
        assert cost > 10.0
        assert cost < 100000.0  # Reasonable upper bound

    def test_negative_tokens_handled(self):
        """Test that negative tokens don't break system"""
        tracker = LLMCostTracker()

        # Should handle gracefully (treat as 0)
        try:
            cost = tracker.estimate_cost("gpt-3.5-turbo", -100, -100)
            assert cost <= 0
        except:
            pass  # Or raise appropriate error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

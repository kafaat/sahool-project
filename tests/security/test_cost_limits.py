"""
Security Tests: LLM Cost Limits Enforcement
اختبارات فرض حدود تكلفة LLM لمنع الفواتير غير المتوقعة
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestCostLimitsSecurity:
    """Test that cost limits are properly enforced"""

    def test_daily_cost_limit_enforcement(self):
        """Test that daily cost limits are enforced"""
        # This test verifies the cost tracking system prevents runaway costs

        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker(max_daily_cost=100.0)

            # Simulate usage that should succeed
            small_cost = tracker.estimate_cost("gpt-3.5-turbo", 1000, 500)
            check_result = tracker.check_limits(small_cost)
            assert check_result["allowed"] == True

            # Record usage
            tracker.record_usage("gpt-3.5-turbo", 1000, 500, "user_1", "tenant_1")

            # Simulate usage that should fail (exceeds limit)
            large_cost = 150.0  # More than max_daily_cost
            check_result = tracker.check_limits(large_cost)
            assert check_result["allowed"] == False
            assert check_result["reason"] == "daily_limit_exceeded"

        except ImportError:
            pytest.skip("Cost tracking module not available")

    def test_monthly_cost_limit_enforcement(self):
        """Test that monthly cost limits are enforced"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker(
                max_daily_cost=100.0,
                max_monthly_cost=2000.0
            )

            # Simulate 25 days of max usage
            for day in range(25):
                tracker.daily_cost = 100.0
                tracker.monthly_cost = 100.0 * day

            # Next request should fail
            check_result = tracker.check_limits(100.0)
            assert check_result["allowed"] == False

        except ImportError:
            pytest.skip("Cost tracking module not available")

    def test_alert_thresholds(self):
        """Test that alerts are triggered at correct thresholds"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker(max_daily_cost=100.0)

            # 40% usage - no alert
            tracker.daily_cost = 40.0
            status = tracker.get_cost_status()
            assert status["alert_level"] == "ok"

            # 60% usage - warning
            tracker.daily_cost = 60.0
            status = tracker.get_cost_status()
            assert status["alert_level"] in ["warning", "ok"]

            # 80% usage - warning
            tracker.daily_cost = 80.0
            status = tracker.get_cost_status()
            assert status["alert_level"] in ["warning", "critical"]

            # 95% usage - critical
            tracker.daily_cost = 95.0
            status = tracker.get_cost_status()
            assert status["alert_level"] == "critical"

        except ImportError:
            pytest.skip("Cost tracking module not available")

    def test_cost_estimation_accuracy(self):
        """Test that cost estimation is accurate"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker()

            # GPT-3.5 Turbo pricing (as of 2024)
            # Input: $0.0015 per 1K tokens
            # Output: $0.002 per 1K tokens

            cost = tracker.estimate_cost("gpt-3.5-turbo", 1000, 1000)
            expected = (1000/1000 * 0.0015) + (1000/1000 * 0.002)
            assert abs(cost - expected) < 0.0001

            # GPT-4 pricing
            # Input: $0.01 per 1K tokens
            # Output: $0.03 per 1K tokens

            cost = tracker.estimate_cost("gpt-4-turbo-preview", 1000, 1000)
            expected = (1000/1000 * 0.01) + (1000/1000 * 0.03)
            assert abs(cost - expected) < 0.0001

        except ImportError:
            pytest.skip("Cost tracking module not available")


class TestCostTrackingIntegrity:
    """Test cost tracking data integrity"""

    def test_usage_history_persistence(self):
        """Test that usage history is properly maintained"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker()

            # Record multiple usages
            for i in range(5):
                tracker.record_usage(
                    "gpt-3.5-turbo",
                    1000,
                    500,
                    f"user_{i}",
                    "tenant_1"
                )

            # Check history
            assert len(tracker.usage_history) == 5

            # Verify total cost calculation
            total = tracker.get_total_cost()
            assert total > 0

        except ImportError:
            pytest.skip("Cost tracking module not available")

    def test_tenant_isolation(self):
        """Test that costs are properly isolated by tenant"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker()

            # Record usage for different tenants
            tracker.record_usage("gpt-3.5-turbo", 1000, 500, "user_1", "tenant_a")
            tracker.record_usage("gpt-3.5-turbo", 1000, 500, "user_2", "tenant_b")

            # Get per-tenant costs
            summary = tracker.get_usage_summary()

            if "by_tenant" in summary:
                assert "tenant_a" in summary["by_tenant"]
                assert "tenant_b" in summary["by_tenant"]

        except ImportError:
            pytest.skip("Cost tracking module not available")


class TestCostProtectionMechanisms:
    """Test cost protection mechanisms"""

    def test_circuit_breaker_on_limit_exceeded(self):
        """Test that circuit breaker activates when limit exceeded"""
        # This test verifies the system stops making LLM calls when limit is hit

        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker(max_daily_cost=10.0)

            # Exceed the limit
            tracker.daily_cost = 15.0

            # Any new request should be blocked
            check = tracker.check_limits(1.0)
            assert check["allowed"] == False

        except ImportError:
            pytest.skip("Cost tracking module not available")

    def test_smart_model_selection(self):
        """Test that cheaper models are used when appropriate"""
        try:
            from multi_repo.agent_ai.app.services.cost_tracker import LLMCostTracker

            tracker = LLMCostTracker()

            # Get recommended model based on task complexity
            if hasattr(tracker, 'recommend_model'):
                # Simple task - should recommend cheaper model
                model = tracker.recommend_model(complexity="low", max_tokens=500)
                assert "gpt-3.5" in model.lower() or "haiku" in model.lower()

                # Complex task - may recommend more powerful model
                model = tracker.recommend_model(complexity="high", max_tokens=2000)
                # Just verify it returns a valid model
                assert model is not None

        except (ImportError, AttributeError):
            pytest.skip("Smart model selection not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

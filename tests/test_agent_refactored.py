"""
Tests for Refactored Agent-AI Modules
Tests retriever and generator separately
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the agent-ai path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'multi-repo', 'agent-ai'))

from app.services.retriever import KnowledgeRetriever
from app.services.generator import ResponseGenerator
from app.services.langchain_agent_refactored import AgriculturalAgent


class TestKnowledgeRetriever:
    """Test retriever module independently"""

    def test_format_field_data_with_soil(self):
        """Test formatting field data with soil information"""
        retriever = KnowledgeRetriever()

        field_data = {
            "soil_summary": {
                "ph_avg": 6.5,
                "ec_avg": 2.3,
                "moisture_avg": 35.2
            }
        }

        formatted = retriever.format_field_data(field_data)

        assert "بيانات التربة" in formatted
        assert "pH: 6.5" in formatted
        assert "EC: 2.3" in formatted
        assert "الرطوبة: 35.2%" in formatted

    def test_format_field_data_with_weather(self):
        """Test formatting field data with weather information"""
        retriever = KnowledgeRetriever()

        field_data = {
            "weather_forecast": {
                "points": [
                    {"temp_c": 32, "rain_mm": 5.2},
                    {"temp_c": 28, "rain_mm": 0.0},
                ]
            }
        }

        formatted = retriever.format_field_data(field_data)

        assert "توقعات الطقس" in formatted
        assert "32" in formatted
        assert "5.2مم" in formatted

    def test_format_field_data_with_ndvi(self):
        """Test formatting field data with NDVI information"""
        retriever = KnowledgeRetriever()

        field_data = {
            "imagery_latest": {
                "ndvi_avg": 0.72
            }
        }

        formatted = retriever.format_field_data(field_data)

        assert "بيانات NDVI" in formatted
        assert "0.72" in formatted

    def test_format_field_data_empty(self):
        """Test formatting empty field data"""
        retriever = KnowledgeRetriever()
        formatted = retriever.format_field_data({})

        assert "لا توجد بيانات متوفرة" in formatted

    def test_extract_soil_metrics(self):
        """Test extracting soil metrics"""
        retriever = KnowledgeRetriever()

        field_data = {
            "soil_summary": {
                "ph_avg": 7.2,
                "ec_avg": 1.5,
                "moisture_avg": 28.0
            }
        }

        metrics = retriever.extract_soil_metrics(field_data)

        assert metrics["ph"] == 7.2
        assert metrics["ec"] == 1.5
        assert metrics["moisture"] == 28.0

    def test_extract_weather_metrics(self):
        """Test extracting weather metrics"""
        retriever = KnowledgeRetriever()

        field_data = {
            "weather_forecast": {
                "points": [
                    {"temp_c": 32, "rain_mm": 5.2, "humidity": 65},
                    {"temp_c": 28, "rain_mm": 0.0, "humidity": 70},
                    {"temp_c": 30, "rain_mm": 2.1, "humidity": 68},
                ]
            }
        }

        metrics = retriever.extract_weather_metrics(field_data)

        assert metrics["max_temp"] == 32
        assert metrics["min_temp"] == 28
        assert metrics["total_rain"] == 7.3
        assert metrics["avg_humidity"] == pytest.approx(67.67, 0.1)

    def test_extract_ndvi_metrics(self):
        """Test extracting NDVI metrics"""
        retriever = KnowledgeRetriever()

        field_data = {
            "imagery_latest": {
                "ndvi_avg": 0.68,
                "ndvi_min": 0.42,
                "ndvi_max": 0.85
            }
        }

        metrics = retriever.extract_ndvi_metrics(field_data)

        assert metrics["ndvi_avg"] == 0.68
        assert metrics["ndvi_min"] == 0.42
        assert metrics["ndvi_max"] == 0.85

    def test_build_retrieval_context(self):
        """Test building complete retrieval context"""
        retriever = KnowledgeRetriever()

        field_data = {
            "soil_summary": {"ph_avg": 6.8, "ec_avg": 2.0},
            "imagery_latest": {"ndvi_avg": 0.65}
        }

        context = retriever.build_retrieval_context(
            query="تحليل الحقل",
            field_data=field_data
        )

        assert "knowledge_context" in context
        assert "field_summary" in context
        assert "soil_metrics" in context
        assert "weather_metrics" in context
        assert "ndvi_metrics" in context


class TestResponseGenerator:
    """Test generator module independently"""

    def test_generator_initialization_with_llm(self):
        """Test generator initializes correctly"""
        generator = ResponseGenerator(llm_provider="fallback")

        assert generator.llm_provider == "fallback"
        assert generator.system_prompt is not None
        assert generator.rag_prompt is not None

    def test_is_llm_available_fallback(self):
        """Test LLM availability check for fallback"""
        generator = ResponseGenerator(llm_provider="fallback")
        assert generator.is_llm_available is False

    def test_generate_rule_based_high_salinity(self):
        """Test rule-based generation for high salinity"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data = {
            "soil_summary": {
                "ec_avg": 5.0  # High salinity
            }
        }

        response = generator.generate_rule_based(field_data)

        assert "🔴" in response  # Critical warning
        assert "ملوحة التربة مرتفعة جداً" in response
        assert "عاجل" in response

    def test_generate_rule_based_low_moisture(self):
        """Test rule-based generation for low moisture"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data = {
            "soil_summary": {
                "moisture_avg": 15.0  # Low moisture
            }
        }

        response = generator.generate_rule_based(field_data)

        assert "💧" in response
        assert "رطوبة التربة منخفضة" in response
        assert "الري" in response

    def test_generate_rule_based_low_ndvi(self):
        """Test rule-based generation for low NDVI"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data = {
            "imagery_latest": {
                "ndvi_avg": 0.3  # Low NDVI
            }
        }

        response = generator.generate_rule_based(field_data)

        assert "🔴" in response
        assert "NDVI منخفض" in response
        assert "عاجل" in response

    def test_generate_rule_based_high_temperature(self):
        """Test rule-based generation for high temperature"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data = {
            "weather_forecast": {
                "points": [
                    {"temp_c": 42, "rain_mm": 0}
                ]
            }
        }

        response = generator.generate_rule_based(field_data)

        assert "🌡️" in response
        assert "درجات حرارة مرتفعة" in response

    def test_generate_rule_based_all_good(self):
        """Test rule-based generation when all metrics are good"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data = {
            "soil_summary": {
                "ph_avg": 6.5,
                "ec_avg": 1.5,
                "moisture_avg": 35.0
            },
            "imagery_latest": {
                "ndvi_avg": 0.75
            }
        }

        response = generator.generate_rule_based(field_data)

        assert "🟢" in response
        assert "الوضع جيد" in response or "الحالة العامة مستقرة" in response

    @pytest.mark.asyncio
    async def test_generate_fallback_on_llm_error(self):
        """Test that generate falls back to rule-based on LLM error"""
        generator = ResponseGenerator(llm_provider="fallback")

        field_data_dict = {
            "soil_summary": {"ec_avg": 2.0}
        }

        response = await generator.generate(
            context="test context",
            field_data="formatted data",
            field_data_dict=field_data_dict,
            question="test",
            use_llm=True
        )

        # Should use rule-based since LLM not available
        assert isinstance(response, str)
        assert len(response) > 0


class TestAgriculturalAgentOrchestration:
    """Test agent orchestration logic"""

    @pytest.mark.asyncio
    async def test_analyze_field_with_mock_dependencies(self):
        """Test agent orchestration with mocked retriever and generator"""

        # Create mock retriever
        mock_retriever = Mock()
        mock_retriever.build_retrieval_context.return_value = {
            "knowledge_context": "test context",
            "field_summary": "test summary",
            "soil_metrics": {"ph": 6.5},
            "weather_metrics": {"max_temp": 30},
            "ndvi_metrics": {"ndvi_avg": 0.7}
        }

        # Create mock generator
        mock_generator = Mock()
        mock_generator.is_llm_available = False
        mock_generator.generate = AsyncMock(return_value="Generated response")

        # Create agent with mocks
        agent = AgriculturalAgent(
            llm_provider="test",
            retriever=mock_retriever,
            generator=mock_generator
        )

        # Test analyze_field
        result = await agent.analyze_field(
            field_id=123,
            field_data={"test": "data"},
            query="test query"
        )

        # Verify orchestration
        mock_retriever.build_retrieval_context.assert_called_once_with(
            query="test query",
            field_data={"test": "data"}
        )
        mock_generator.generate.assert_called_once()

        assert result["field_id"] == 123
        assert result["analysis"] == "Generated response"
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_chat_without_llm(self):
        """Test chat when LLM is not available"""
        mock_generator = Mock()
        mock_generator.is_llm_available = False

        agent = AgriculturalAgent(
            llm_provider="fallback",
            generator=mock_generator
        )

        result = await agent.chat(
            message="test message",
            field_data=None
        )

        assert result["llm_available"] is False
        assert "غير متوفرة" in result["response"]

    def test_get_metrics_summary(self):
        """Test metrics summary extraction"""
        mock_retriever = Mock()
        mock_retriever.extract_soil_metrics.return_value = {"ph": 6.5}
        mock_retriever.extract_weather_metrics.return_value = {"max_temp": 32}
        mock_retriever.extract_ndvi_metrics.return_value = {"ndvi_avg": 0.7}

        agent = AgriculturalAgent(
            retriever=mock_retriever,
            generator=Mock()
        )

        field_data = {"test": "data"}
        summary = agent.get_metrics_summary(field_data)

        assert summary["soil"]["ph"] == 6.5
        assert summary["weather"]["max_temp"] == 32
        assert summary["ndvi"]["ndvi_avg"] == 0.7


class TestIntegration:
    """Integration tests for the complete refactored system"""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self):
        """Test complete analysis flow with real components"""

        # Use real retriever and generator (fallback mode)
        agent = AgriculturalAgent(llm_provider="fallback")

        field_data = {
            "soil_summary": {
                "ph_avg": 7.2,
                "ec_avg": 5.5,  # High salinity - should trigger warning
                "moisture_avg": 18.0  # Low moisture - should trigger warning
            },
            "imagery_latest": {
                "ndvi_avg": 0.35  # Low NDVI - should trigger critical
            },
            "weather_forecast": {
                "points": [
                    {"temp_c": 41, "rain_mm": 0},  # High temp
                ]
            }
        }

        result = await agent.analyze_field(
            field_id=999,
            field_data=field_data,
            query="قدم تحليل شامل"
        )

        # Verify result structure
        assert result["field_id"] == 999
        assert "analysis" in result
        assert "metrics" in result

        # Verify analysis content
        analysis = result["analysis"]
        assert "🔴" in analysis  # Critical warning should be present
        assert "ملوحة" in analysis or "NDVI" in analysis  # Should mention issues

        # Verify metrics were extracted
        assert "soil" in result["metrics"]
        assert "weather" in result["metrics"]
        assert "ndvi" in result["metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for Advisor Core Service
سهول اليمن - اختبارات خدمة المستشار الزراعي
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self):
        """Health endpoint should return 200"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self):
        """Health endpoint should return healthy status"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "advisor-core"

    def test_health_check_includes_ai_status(self):
        """Health endpoint should include AI status"""
        response = client.get("/health")
        data = response.json()
        assert "ai_enabled" in data


class TestAnalyzeFieldEndpoint:
    """Test field analysis endpoint"""

    def test_analyze_field_returns_200(self):
        """Analyze field endpoint should return 200"""
        payload = {"field_id": 1}
        response = client.post("/api/v1/advisor/analyze-field", json=payload)
        assert response.status_code == 200

    def test_analyze_field_returns_valid_structure(self):
        """Analyze field should return valid structure"""
        payload = {"field_id": 1}
        response = client.post("/api/v1/advisor/analyze-field", json=payload)
        data = response.json()

        assert "field_id" in data
        assert "analysis_id" in data
        assert "recommendations" in data
        assert "ndvi_snapshot" in data
        assert "weather_snapshot" in data
        assert "overall_status" in data
        assert "risk_level" in data

    def test_analyze_field_recommendations_structure(self):
        """Recommendations should have correct structure"""
        payload = {"field_id": 1}
        response = client.post("/api/v1/advisor/analyze-field", json=payload)
        data = response.json()

        for rec in data["recommendations"]:
            assert "id" in rec
            assert "priority" in rec
            assert "category" in rec
            assert "title_ar" in rec
            assert "title_en" in rec
            assert "description_ar" in rec
            assert "description_en" in rec
            assert "actions" in rec

    def test_analyze_field_with_low_ndvi(self):
        """Low NDVI should generate high priority recommendations"""
        payload = {"field_id": 1, "ndvi_value": 0.2}
        response = client.post("/api/v1/advisor/analyze-field", json=payload)
        data = response.json()

        assert data["risk_level"] == "high"
        # Should have at least one high priority recommendation
        high_priority = [r for r in data["recommendations"] if r["priority"] == "high"]
        assert len(high_priority) > 0

    def test_analyze_field_with_good_ndvi(self):
        """Good NDVI should have low risk"""
        payload = {"field_id": 1, "ndvi_value": 0.7}
        response = client.post("/api/v1/advisor/analyze-field", json=payload)
        data = response.json()

        assert data["risk_level"] == "low"


class TestIrrigationAdviceEndpoint:
    """Test irrigation advice endpoint"""

    def test_get_irrigation_advice_returns_200(self):
        """Irrigation advice endpoint should return 200"""
        response = client.get("/api/v1/advisor/irrigation/1")
        assert response.status_code == 200

    def test_get_irrigation_advice_returns_valid_structure(self):
        """Irrigation advice should return valid structure"""
        response = client.get("/api/v1/advisor/irrigation/1")
        data = response.json()

        assert "field_id" in data
        assert "recommended_amount_mm" in data
        assert "recommended_time" in data
        assert "frequency_days" in data
        assert "method" in data
        assert "reasoning_ar" in data

    def test_get_irrigation_advice_amount_positive(self):
        """Irrigation amount should be positive"""
        response = client.get("/api/v1/advisor/irrigation/1")
        data = response.json()
        assert data["recommended_amount_mm"] > 0

    def test_get_irrigation_advice_with_crop_type(self):
        """Should accept crop_type parameter"""
        response = client.get("/api/v1/advisor/irrigation/1?crop_type=قمح")
        assert response.status_code == 200

    def test_get_irrigation_advice_valid_method(self):
        """Irrigation method should be valid"""
        response = client.get("/api/v1/advisor/irrigation/1")
        data = response.json()
        valid_methods = ["تنقيط", "رش", "غمر"]
        assert data["method"] in valid_methods


class TestPestAlertsEndpoint:
    """Test pest alerts endpoint"""

    def test_get_pest_alerts_returns_200(self):
        """Pest alerts endpoint should return 200"""
        response = client.get("/api/v1/advisor/pest-alerts")
        assert response.status_code == 200

    def test_get_pest_alerts_returns_list(self):
        """Pest alerts should return list"""
        response = client.get("/api/v1/advisor/pest-alerts")
        data = response.json()
        assert isinstance(data, list)

    def test_get_pest_alerts_structure(self):
        """Pest alerts should have correct structure"""
        response = client.get("/api/v1/advisor/pest-alerts")
        data = response.json()

        for alert in data:
            assert "pest_name_ar" in alert
            assert "pest_name_en" in alert
            assert "risk_level" in alert
            assert "affected_crops" in alert
            assert "prevention_ar" in alert
            assert "treatment_ar" in alert

    def test_get_pest_alerts_with_region_filter(self):
        """Should accept region_id filter"""
        response = client.get("/api/v1/advisor/pest-alerts?region_id=1")
        assert response.status_code == 200

    def test_get_pest_alerts_with_crop_filter(self):
        """Should accept crop_type filter"""
        response = client.get("/api/v1/advisor/pest-alerts?crop_type=طماطم")
        assert response.status_code == 200


class TestCropRecommendationsEndpoint:
    """Test crop recommendations endpoint"""

    def test_get_crop_recommendations_returns_200(self):
        """Crop recommendations endpoint should return 200"""
        response = client.get("/api/v1/advisor/crop-recommendations?region_id=1")
        assert response.status_code == 200

    def test_get_crop_recommendations_returns_list(self):
        """Crop recommendations should return list"""
        response = client.get("/api/v1/advisor/crop-recommendations?region_id=1")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_crop_recommendations_structure(self):
        """Crop recommendations should have correct structure"""
        response = client.get("/api/v1/advisor/crop-recommendations?region_id=1")
        data = response.json()

        for crop in data:
            assert "crop_name_ar" in crop
            assert "crop_name_en" in crop
            assert "suitability_score" in crop
            assert "expected_yield_kg_ha" in crop
            assert "water_requirement" in crop
            assert "growing_season" in crop
            assert "notes_ar" in crop

    def test_get_crop_recommendations_sorted_by_suitability(self):
        """Recommendations should be sorted by suitability score"""
        response = client.get("/api/v1/advisor/crop-recommendations?region_id=1")
        data = response.json()

        for i in range(len(data) - 1):
            assert data[i]["suitability_score"] >= data[i + 1]["suitability_score"]

    def test_get_crop_recommendations_suitability_range(self):
        """Suitability score should be between 0 and 1"""
        response = client.get("/api/v1/advisor/crop-recommendations?region_id=1")
        data = response.json()

        for crop in data:
            assert 0 <= crop["suitability_score"] <= 1


class TestAskAdvisorEndpoint:
    """Test ask advisor (AI) endpoint"""

    def test_ask_advisor_returns_200(self):
        """Ask advisor endpoint should return 200"""
        payload = {"question": "ما هو أفضل وقت للري؟"}
        response = client.post("/api/v1/advisor/ask", json=payload)
        assert response.status_code == 200

    def test_ask_advisor_returns_valid_structure(self):
        """Ask advisor should return valid structure"""
        payload = {"question": "كيف أحسن التربة؟"}
        response = client.post("/api/v1/advisor/ask", json=payload)
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "confidence" in data
        assert "sources" in data

    def test_ask_advisor_returns_answer(self):
        """Ask advisor should return an answer"""
        payload = {"question": "ما هي أفضل طريقة للري؟"}
        response = client.post("/api/v1/advisor/ask", json=payload)
        data = response.json()

        assert len(data["answer"]) > 0

    def test_ask_advisor_confidence_range(self):
        """Confidence should be between 0 and 1"""
        payload = {"question": "سؤال اختباري"}
        response = client.post("/api/v1/advisor/ask", json=payload)
        data = response.json()

        assert 0 <= data["confidence"] <= 1

    def test_ask_advisor_irrigation_question(self):
        """Should respond to irrigation questions"""
        payload = {"question": "كيف أري الحقل؟"}
        response = client.post("/api/v1/advisor/ask", json=payload)
        data = response.json()
        assert "ري" in data["answer"].lower() or "الري" in data["answer"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
API Tests for Field Advisor Service
"""
import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.advisor import (
    RecommendationType,
    AlertSeverity,
    NDVITrend,
    RiskLevel,
)


client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "field-advisor-service"

    def test_liveness_probe(self):
        """Test liveness probe"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe(self):
        """Test readiness probe"""
        response = client.get("/health/ready")
        assert response.status_code == 200


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_service_info(self):
        """Test root endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "field-advisor-service"
        assert "endpoints" in data
        assert "analyze" in data["endpoints"]


class TestAnalyzeField:
    """Test field analysis endpoint"""

    def test_analyze_field_basic(self):
        """Test basic field analysis"""
        field_id = str(uuid4())
        response = client.post(
            "/advisor/analyze-field",
            json={
                "field_id": field_id,
                "include_weather": True,
                "include_forecast": True,
                "language": "en",
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert data["field_id"] == field_id
        assert "health_score" in data
        assert 0 <= data["health_score"] <= 100
        assert "risk_level" in data
        assert "recommendations" in data
        assert "alerts" in data
        assert "summary" in data

    def test_analyze_field_with_ndvi_override(self):
        """Test analysis with NDVI data override"""
        field_id = str(uuid4())
        response = client.post(
            "/advisor/analyze-field",
            json={
                "field_id": field_id,
                "ndvi_data": {
                    "mean": 0.25,  # Critical level
                    "min": 0.1,
                    "max": 0.4,
                    "trend": "declining"
                },
                "language": "en",
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should have critical alerts due to low NDVI
        assert data["critical_alerts"] >= 1
        assert data["risk_level"] in ["high", "critical"]

    def test_analyze_field_arabic_language(self):
        """Test analysis with Arabic language"""
        field_id = str(uuid4())
        response = client.post(
            "/advisor/analyze-field",
            json={
                "field_id": field_id,
                "language": "ar",
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should have Arabic content
        assert "summary_ar" in data
        if data["recommendations"]:
            assert data["recommendations"][0].get("title_ar") is not None

    def test_analyze_field_with_weather_override(self):
        """Test analysis with weather data override"""
        field_id = str(uuid4())
        response = client.post(
            "/advisor/analyze-field",
            json={
                "field_id": field_id,
                "weather_data": {
                    "temperature_current": 42.0,  # High temp
                    "humidity": 25.0,  # Low humidity
                    "wind_speed": 55.0,  # High wind
                },
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should have weather-related alerts
        alert_types = [a["alert_type"] for a in data["alerts"]]
        assert any("temperature" in t or "wind" in t for t in alert_types)


class TestRecommendations:
    """Test recommendations endpoints"""

    def test_get_recommendations_empty(self):
        """Test getting recommendations for field with no data"""
        field_id = str(uuid4())
        response = client.get(f"/advisor/recommendations/{field_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_recommendations_filtered_by_type(self):
        """Test filtering recommendations by type"""
        field_id = str(uuid4())

        # First analyze to create recommendations
        client.post(
            "/advisor/analyze-field",
            json={"field_id": field_id}
        )

        response = client.get(
            f"/advisor/recommendations/{field_id}",
            params={"type": "irrigation"}
        )
        assert response.status_code == 200


class TestAlerts:
    """Test alerts endpoints"""

    def test_get_alerts_empty(self):
        """Test getting alerts for field with no data"""
        field_id = str(uuid4())
        response = client.get(f"/advisor/alerts/{field_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_alerts_filtered_by_severity(self):
        """Test filtering alerts by severity"""
        field_id = str(uuid4())
        response = client.get(
            f"/advisor/alerts/{field_id}",
            params={"severity": "critical"}
        )
        assert response.status_code == 200


class TestPlaybook:
    """Test playbook endpoints"""

    def test_generate_playbook(self):
        """Test generating action playbook"""
        field_id = str(uuid4())

        # First analyze to create recommendations
        client.post(
            "/advisor/analyze-field",
            json={"field_id": field_id}
        )

        response = client.post(
            "/advisor/playbook",
            json={
                "field_id": field_id,
                "time_horizon_days": 14,
                "include_resources": True,
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["field_id"] == field_id
        assert "actions" in data
        assert "generated_at" in data
        assert data["time_horizon_days"] == 14


class TestStats:
    """Test statistics endpoints"""

    def test_get_field_stats(self):
        """Test getting field statistics"""
        field_id = str(uuid4())

        # First analyze to create data
        client.post(
            "/advisor/analyze-field",
            json={"field_id": field_id}
        )

        response = client.get(f"/advisor/stats/{field_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["field_id"] == field_id
        assert "recommendations" in data
        assert "alerts" in data
        assert "actions" in data
        assert "last_analysis" in data


class TestRequestHeaders:
    """Test request/response headers"""

    def test_request_id_header(self):
        """Test that X-Request-ID is returned"""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_response_time_header(self):
        """Test that X-Response-Time is returned"""
        response = client.get("/health")
        assert "X-Response-Time" in response.headers


class TestValidation:
    """Test input validation"""

    def test_invalid_field_id(self):
        """Test with invalid field ID format"""
        response = client.post(
            "/advisor/analyze-field",
            json={"field_id": "not-a-uuid"}
        )
        assert response.status_code == 422

    def test_invalid_ndvi_values(self):
        """Test with invalid NDVI values"""
        response = client.post(
            "/advisor/analyze-field",
            json={
                "field_id": str(uuid4()),
                "ndvi_data": {
                    "mean": 2.0,  # Invalid: > 1
                    "min": 0.1,
                    "max": 0.5,
                }
            }
        )
        assert response.status_code == 422

    def test_invalid_playbook_horizon(self):
        """Test with invalid time horizon"""
        response = client.post(
            "/advisor/playbook",
            json={
                "field_id": str(uuid4()),
                "time_horizon_days": 100,  # Invalid: > 90
            }
        )
        assert response.status_code == 422

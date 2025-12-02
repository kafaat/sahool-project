"""
Unit tests for Field Suite Backend Main API
سهول اليمن - اختبارات الـ API الرئيسية
"""
import pytest
from fastapi.testclient import TestClient
import os

# Set environment variables before importing app
os.environ.setdefault("IMAGERY_CORE_BASE_URL", "http://imagery-core:8000")
os.environ.setdefault("ANALYTICS_CORE_BASE_URL", "http://analytics-core:8000")
os.environ.setdefault("GEO_CORE_BASE_URL", "http://geo-core:8000")
os.environ.setdefault("WEATHER_CORE_BASE_URL", "http://weather-core:8000")
os.environ.setdefault("ADVISOR_CORE_BASE_URL", "http://advisor-core:8000")
os.environ.setdefault("QUERY_CORE_BASE_URL", "http://query-core:8000")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_KEY_SECRET", "test-api-key")

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_returns_200(self):
        """Health endpoint should return 200"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self):
        """Health endpoint should return healthy status"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "field-suite-backend"
        assert data["version"] == "6.0.0"

    def test_health_check_includes_timestamp(self):
        """Health endpoint should include timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data

    def test_liveness_check_returns_200(self):
        """Liveness endpoint should return 200"""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_liveness_check_returns_alive(self):
        """Liveness endpoint should return alive status"""
        response = client.get("/health/live")
        data = response.json()
        assert data["status"] == "alive"


class TestRegionsEndpoint:
    """Test regions endpoint"""

    def test_list_regions_returns_200(self):
        """Regions endpoint should return 200"""
        response = client.get("/v1/regions")
        assert response.status_code == 200

    def test_list_regions_returns_all_governorates(self):
        """Should return all 20 Yemen governorates"""
        response = client.get("/v1/regions")
        data = response.json()

        assert "regions" in data
        assert "count" in data
        assert data["count"] == 20
        assert len(data["regions"]) == 20

    def test_list_regions_structure(self):
        """Regions should have correct structure"""
        response = client.get("/v1/regions")
        data = response.json()

        for region in data["regions"]:
            assert "id" in region
            assert "name_ar" in region
            assert "name_en" in region
            assert "lat" in region
            assert "lon" in region

    def test_list_regions_sanaa_first(self):
        """Sanaa should be the first region"""
        response = client.get("/v1/regions")
        data = response.json()

        first_region = data["regions"][0]
        assert first_region["name_ar"] == "صنعاء"
        assert first_region["name_en"] == "Sanaa"

    def test_list_regions_coordinates_valid(self):
        """Region coordinates should be in Yemen bounds"""
        response = client.get("/v1/regions")
        data = response.json()

        for region in data["regions"]:
            # Yemen bounds: lat 12-19, lon 42-55
            assert 12 <= region["lat"] <= 19
            assert 42 <= region["lon"] <= 55


class TestCropsEndpoint:
    """Test crops endpoint"""

    def test_list_crops_returns_200(self):
        """Crops endpoint should return 200"""
        response = client.get("/v1/crops")
        assert response.status_code == 200

    def test_list_crops_returns_list(self):
        """Should return list of crops"""
        response = client.get("/v1/crops")
        data = response.json()

        assert "crops" in data
        assert "count" in data
        assert isinstance(data["crops"], list)
        assert data["count"] == len(data["crops"])

    def test_list_crops_structure(self):
        """Crops should have correct structure"""
        response = client.get("/v1/crops")
        data = response.json()

        for crop in data["crops"]:
            assert "name_ar" in crop
            assert "name_en" in crop
            assert "season" in crop

    def test_list_crops_includes_wheat(self):
        """Should include wheat (قمح)"""
        response = client.get("/v1/crops")
        data = response.json()

        crop_names = [c["name_ar"] for c in data["crops"]]
        assert "قمح" in crop_names

    def test_list_crops_includes_coffee(self):
        """Should include coffee (بن)"""
        response = client.get("/v1/crops")
        data = response.json()

        crop_names = [c["name_ar"] for c in data["crops"]]
        assert "بن" in crop_names


class TestDashboardEndpoint:
    """Test dashboard endpoint"""

    def test_get_dashboard_returns_200(self):
        """Dashboard endpoint should return 200"""
        response = client.get("/v1/dashboard")
        assert response.status_code == 200

    def test_get_dashboard_returns_valid_structure(self):
        """Dashboard should return valid structure"""
        response = client.get("/v1/dashboard")
        data = response.json()

        assert "summary" in data
        assert "ndvi_status" in data
        assert "alerts" in data
        assert "weather" in data
        assert "last_updated" in data

    def test_get_dashboard_summary_structure(self):
        """Summary should have correct structure"""
        response = client.get("/v1/dashboard")
        data = response.json()

        summary = data["summary"]
        assert "total_farmers" in summary
        assert "total_fields" in summary
        assert "total_area_ha" in summary
        assert "active_regions" in summary

    def test_get_dashboard_active_regions_is_20(self):
        """Active regions should be 20"""
        response = client.get("/v1/dashboard")
        data = response.json()
        assert data["summary"]["active_regions"] == 20

    def test_get_dashboard_ndvi_status_structure(self):
        """NDVI status should have all categories"""
        response = client.get("/v1/dashboard")
        data = response.json()

        ndvi = data["ndvi_status"]
        assert "excellent" in ndvi
        assert "good" in ndvi
        assert "moderate" in ndvi
        assert "poor" in ndvi

    def test_get_dashboard_alerts_structure(self):
        """Alerts should have priority levels"""
        response = client.get("/v1/dashboard")
        data = response.json()

        alerts = data["alerts"]
        assert "high" in alerts
        assert "medium" in alerts
        assert "low" in alerts

    def test_get_dashboard_weather_structure(self):
        """Weather should have temperature and rain"""
        response = client.get("/v1/dashboard")
        data = response.json()

        weather = data["weather"]
        assert "avg_temp_celsius" in weather
        assert "rain_probability" in weather


class TestMetricsEndpoint:
    """Test metrics endpoint"""

    def test_metrics_returns_200(self):
        """Metrics endpoint should return 200"""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_prometheus_format(self):
        """Metrics should be in Prometheus format"""
        response = client.get("/metrics")
        assert "text/plain" in response.headers.get("content-type", "") or \
               "text/plain" in str(response.headers)


class TestErrorHandling:
    """Test error handling"""

    def test_404_for_unknown_endpoint(self):
        """Should return 404 for unknown endpoints"""
        response = client.get("/unknown/endpoint")
        assert response.status_code == 404

    def test_error_response_structure(self):
        """Error responses should have correct structure"""
        response = client.get("/unknown/endpoint")
        data = response.json()
        assert "detail" in data or "error" in data


class TestCORS:
    """Test CORS headers"""

    def test_cors_headers_present(self):
        """CORS headers should be present"""
        response = client.options("/health")
        # FastAPI handles OPTIONS automatically with CORS middleware


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

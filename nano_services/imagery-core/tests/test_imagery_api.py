"""
Unit tests for Imagery Core Service
سهول اليمن - اختبارات خدمة الصور
"""
import pytest
from datetime import date
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
        assert data["service"] == "imagery-core"

    def test_health_check_includes_satellites(self):
        """Health endpoint should include satellite info"""
        response = client.get("/health")
        data = response.json()
        assert "satellites" in data
        assert "Sentinel-2" in data["satellites"]


class TestNDVIEndpoint:
    """Test NDVI tile endpoint"""

    def test_get_ndvi_returns_200(self):
        """NDVI endpoint should return 200 for valid field_id"""
        response = client.get("/api/v1/ndvi/1")
        assert response.status_code == 200

    def test_get_ndvi_returns_valid_structure(self):
        """NDVI endpoint should return valid data structure"""
        response = client.get("/api/v1/ndvi/1")
        data = response.json()

        assert "field_id" in data
        assert "date" in data
        assert "tile_url" in data
        assert "satellite" in data
        assert "cloud_coverage" in data
        assert "ndvi_mean" in data
        assert "ndvi_min" in data
        assert "ndvi_max" in data

    def test_get_ndvi_field_id_matches(self):
        """NDVI endpoint should return correct field_id"""
        field_id = 42
        response = client.get(f"/api/v1/ndvi/{field_id}")
        data = response.json()
        assert data["field_id"] == field_id

    def test_get_ndvi_values_in_range(self):
        """NDVI values should be in valid range [-1, 1]"""
        response = client.get("/api/v1/ndvi/1")
        data = response.json()

        assert -1 <= data["ndvi_min"] <= 1
        assert -1 <= data["ndvi_mean"] <= 1
        assert -1 <= data["ndvi_max"] <= 1
        assert data["ndvi_min"] <= data["ndvi_mean"] <= data["ndvi_max"]

    def test_get_ndvi_cloud_coverage_valid(self):
        """Cloud coverage should be between 0 and 100"""
        response = client.get("/api/v1/ndvi/1")
        data = response.json()
        assert 0 <= data["cloud_coverage"] <= 100

    def test_get_ndvi_tile_url_format(self):
        """Tile URL should have correct format"""
        response = client.get("/api/v1/ndvi/1")
        data = response.json()
        assert "https://" in data["tile_url"]
        assert ".png" in data["tile_url"]

    def test_get_ndvi_with_target_date(self):
        """NDVI endpoint should accept target_date parameter"""
        target_date = "2024-06-15"
        response = client.get(f"/api/v1/ndvi/1?target_date={target_date}")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == target_date

    def test_get_ndvi_with_crop_type(self):
        """NDVI endpoint should accept crop_type parameter"""
        response = client.get("/api/v1/ndvi/1?crop_type=قمح")
        assert response.status_code == 200


class TestNDVIHistoryEndpoint:
    """Test NDVI history endpoint"""

    def test_get_ndvi_history_returns_200(self):
        """NDVI history endpoint should return 200"""
        response = client.get("/api/v1/ndvi/1/history")
        assert response.status_code == 200

    def test_get_ndvi_history_returns_valid_structure(self):
        """NDVI history should return valid structure"""
        response = client.get("/api/v1/ndvi/1/history")
        data = response.json()

        assert "field_id" in data
        assert "history" in data
        assert "trend" in data
        assert "health_status" in data
        assert isinstance(data["history"], list)

    def test_get_ndvi_history_items_structure(self):
        """History items should have correct structure"""
        response = client.get("/api/v1/ndvi/1/history")
        data = response.json()

        for item in data["history"]:
            assert "date" in item
            assert "ndvi_mean" in item
            assert "cloud_coverage" in item
            assert "satellite" in item

    def test_get_ndvi_history_trend_valid(self):
        """Trend should be valid value"""
        response = client.get("/api/v1/ndvi/1/history")
        data = response.json()
        assert data["trend"] in ["improving", "stable", "declining"]

    def test_get_ndvi_history_with_months_param(self):
        """NDVI history should accept months parameter"""
        response = client.get("/api/v1/ndvi/1/history?months=3")
        assert response.status_code == 200


class TestAvailableImageryEndpoint:
    """Test available imagery search endpoint"""

    def test_get_available_imagery_returns_200(self):
        """Available imagery endpoint should return 200"""
        response = client.get("/api/v1/imagery/available?lat=15.35&lon=44.20")
        assert response.status_code == 200

    def test_get_available_imagery_returns_list(self):
        """Available imagery should return list of images"""
        response = client.get("/api/v1/imagery/available?lat=15.35&lon=44.20")
        data = response.json()

        assert "images" in data
        assert "count" in data
        assert isinstance(data["images"], list)

    def test_get_available_imagery_item_structure(self):
        """Image items should have correct structure"""
        response = client.get("/api/v1/imagery/available?lat=15.35&lon=44.20")
        data = response.json()

        if data["images"]:
            image = data["images"][0]
            assert "scene_id" in image
            assert "satellite" in image
            assert "acquisition_date" in image
            assert "cloud_coverage" in image


class TestAnalyzeNDVIEndpoint:
    """Test NDVI analysis endpoint"""

    def test_analyze_ndvi_returns_200(self):
        """Analyze NDVI endpoint should return 200"""
        payload = {"field_id": 1, "geometry": {}}
        response = client.post("/api/v1/ndvi/analyze", json=payload)
        assert response.status_code == 200

    def test_analyze_ndvi_returns_results(self):
        """Analyze NDVI should return analysis results"""
        payload = {"field_id": 1, "geometry": {}}
        response = client.post("/api/v1/ndvi/analyze", json=payload)
        data = response.json()

        assert "field_id" in data
        assert "analysis_id" in data
        assert "status" in data
        assert "results" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

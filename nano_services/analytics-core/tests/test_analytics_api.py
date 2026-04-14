"""
Unit tests for Analytics Core Service
سهول اليمن - اختبارات خدمة التحليلات
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
        assert data["service"] == "analytics-core"


class TestNDVITimelineEndpoint:
    """Test NDVI timeline endpoint"""

    def test_get_ndvi_timeline_returns_200(self):
        """NDVI timeline endpoint should return 200"""
        response = client.get("/api/v1/ndvi/1/timeline")
        assert response.status_code == 200

    def test_get_ndvi_timeline_returns_valid_structure(self):
        """NDVI timeline should return valid structure"""
        response = client.get("/api/v1/ndvi/1/timeline")
        data = response.json()

        assert "field_id" in data
        assert "data" in data
        assert "trend_direction" in data
        assert "trend_strength" in data
        assert isinstance(data["data"], list)

    def test_get_ndvi_timeline_data_structure(self):
        """Timeline data items should have correct structure"""
        response = client.get("/api/v1/ndvi/1/timeline")
        data = response.json()

        for item in data["data"]:
            assert "date" in item
            assert "mean_ndvi" in item
            assert "min_ndvi" in item
            assert "max_ndvi" in item
            assert "std_ndvi" in item

    def test_get_ndvi_timeline_trend_valid(self):
        """Trend direction should be valid"""
        response = client.get("/api/v1/ndvi/1/timeline")
        data = response.json()
        assert data["trend_direction"] in ["ascending", "stable", "descending"]

    def test_get_ndvi_timeline_with_months_param(self):
        """Timeline should accept months parameter"""
        response = client.get("/api/v1/ndvi/1/timeline?months=3")
        assert response.status_code == 200


class TestYieldPredictionEndpoint:
    """Test yield prediction endpoint"""

    def test_get_yield_prediction_returns_200(self):
        """Yield prediction endpoint should return 200"""
        response = client.get("/api/v1/analytics/yield-prediction?field_id=1")
        assert response.status_code == 200

    def test_get_yield_prediction_returns_valid_structure(self):
        """Yield prediction should return valid structure"""
        response = client.get("/api/v1/analytics/yield-prediction?field_id=1")
        data = response.json()

        assert "field_id" in data
        assert "crop_type" in data
        assert "predicted_yield_kg_ha" in data
        assert "confidence_low" in data
        assert "confidence_high" in data
        assert "confidence_percent" in data
        assert "factors" in data

    def test_get_yield_prediction_confidence_range_valid(self):
        """Confidence range should be valid"""
        response = client.get("/api/v1/analytics/yield-prediction?field_id=1")
        data = response.json()

        assert data["confidence_low"] <= data["predicted_yield_kg_ha"]
        assert data["predicted_yield_kg_ha"] <= data["confidence_high"]
        assert 0 <= data["confidence_percent"] <= 100

    def test_get_yield_prediction_with_crop_type(self):
        """Yield prediction should accept crop_type parameter"""
        response = client.get("/api/v1/analytics/yield-prediction?field_id=1&crop_type=قمح")
        assert response.status_code == 200
        data = response.json()
        assert data["crop_type"] == "قمح"


class TestSeasonalAnalysisEndpoint:
    """Test seasonal analysis endpoint"""

    def test_get_seasonal_analysis_returns_200(self):
        """Seasonal analysis endpoint should return 200"""
        response = client.get("/api/v1/analytics/seasonal")
        assert response.status_code == 200

    def test_get_seasonal_analysis_returns_list(self):
        """Seasonal analysis should return list of seasons"""
        response = client.get("/api/v1/analytics/seasonal")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # 4 seasons

    def test_get_seasonal_analysis_structure(self):
        """Season items should have correct structure"""
        response = client.get("/api/v1/analytics/seasonal")
        data = response.json()

        for season in data:
            assert "season" in season
            assert "season_ar" in season
            assert "start_month" in season
            assert "end_month" in season
            assert "recommended_crops" in season
            assert "water_needs" in season
            assert "expected_challenges" in season

    def test_get_seasonal_analysis_valid_months(self):
        """Season months should be valid (1-12)"""
        response = client.get("/api/v1/analytics/seasonal")
        data = response.json()

        for season in data:
            assert 1 <= season["start_month"] <= 12
            assert 1 <= season["end_month"] <= 12


class TestRegionStatsEndpoint:
    """Test region statistics endpoint"""

    def test_get_region_stats_returns_200(self):
        """Region stats endpoint should return 200"""
        response = client.get("/api/v1/analytics/region-stats?region_id=1")
        assert response.status_code == 200

    def test_get_region_stats_returns_valid_structure(self):
        """Region stats should return valid structure"""
        response = client.get("/api/v1/analytics/region-stats?region_id=1")
        data = response.json()

        assert "region_id" in data
        assert "region_name_ar" in data
        assert "total_fields" in data
        assert "total_area_ha" in data
        assert "avg_ndvi" in data
        assert "active_crops" in data
        assert "alerts_count" in data

    def test_get_region_stats_positive_values(self):
        """Stats values should be positive"""
        response = client.get("/api/v1/analytics/region-stats?region_id=1")
        data = response.json()

        assert data["total_fields"] >= 0
        assert data["total_area_ha"] >= 0
        assert data["alerts_count"] >= 0


class TestDashboardStatsEndpoint:
    """Test dashboard statistics endpoint"""

    def test_get_dashboard_stats_returns_200(self):
        """Dashboard stats endpoint should return 200"""
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200

    def test_get_dashboard_stats_returns_valid_structure(self):
        """Dashboard stats should return valid structure"""
        response = client.get("/api/v1/analytics/dashboard")
        data = response.json()

        assert "total_fields" in data
        assert "total_farmers" in data
        assert "total_area_ha" in data
        assert "active_regions" in data
        assert "avg_ndvi_national" in data
        assert "alerts_today" in data
        assert "crop_distribution" in data
        assert "last_updated" in data

    def test_get_dashboard_stats_crop_distribution_valid(self):
        """Crop distribution percentages should sum to ~100"""
        response = client.get("/api/v1/analytics/dashboard")
        data = response.json()

        total = sum(data["crop_distribution"].values())
        assert 95 <= total <= 105  # Allow some tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

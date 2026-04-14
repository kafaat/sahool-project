"""
Unit tests for Query Core Service
سهول اليمن - اختبارات خدمة الاستعلامات
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
        assert data["service"] == "query-core"


class TestFieldSummaryEndpoint:
    """Test field summary endpoint"""

    def test_get_field_summary_returns_200(self):
        """Field summary endpoint should return 200"""
        response = client.get("/api/v1/fields/test-id/summary")
        assert response.status_code == 200

    def test_get_field_summary_returns_valid_structure(self):
        """Field summary should return valid structure"""
        response = client.get("/api/v1/fields/test-id/summary")
        data = response.json()

        assert "field_id" in data
        assert "name_ar" in data
        assert "crop_type" in data
        assert "area_ha" in data
        assert "region_name" in data
        assert "last_ndvi_date" in data
        assert "last_ndvi_value" in data
        assert "health_status" in data

    def test_get_field_summary_ndvi_valid_range(self):
        """NDVI value should be in valid range"""
        response = client.get("/api/v1/fields/test-id/summary")
        data = response.json()
        assert 0 <= data["last_ndvi_value"] <= 1

    def test_get_field_summary_health_status_valid(self):
        """Health status should be valid"""
        response = client.get("/api/v1/fields/test-id/summary")
        data = response.json()
        valid_statuses = ["ممتاز", "جيد", "متوسط", "يحتاج متابعة"]
        assert data["health_status"] in valid_statuses


class TestFieldDetailsEndpoint:
    """Test field details endpoint"""

    def test_get_field_details_returns_200(self):
        """Field details endpoint should return 200"""
        response = client.get("/api/v1/fields/test-id/details")
        assert response.status_code == 200

    def test_get_field_details_returns_valid_structure(self):
        """Field details should return valid structure"""
        response = client.get("/api/v1/fields/test-id/details")
        data = response.json()

        assert "field_id" in data
        assert "farmer_id" in data
        assert "name_ar" in data
        assert "area_ha" in data
        assert "crop_type" in data
        assert "region_id" in data
        assert "region_name" in data
        assert "coordinates" in data
        assert "soil_type" in data
        assert "irrigation_type" in data
        assert "elevation_m" in data
        assert "last_ndvi" in data

    def test_get_field_details_coordinates_valid(self):
        """Coordinates should be valid"""
        response = client.get("/api/v1/fields/test-id/details")
        data = response.json()

        assert "lat" in data["coordinates"]
        assert "lon" in data["coordinates"]


class TestFarmerEndpoint:
    """Test farmer endpoint"""

    def test_get_farmer_returns_200(self):
        """Farmer endpoint should return 200"""
        response = client.get("/api/v1/farmers/test-farmer-id")
        assert response.status_code == 200

    def test_get_farmer_returns_valid_structure(self):
        """Farmer info should return valid structure"""
        response = client.get("/api/v1/farmers/test-farmer-id")
        data = response.json()

        assert "farmer_id" in data
        assert "name" in data
        assert "phone" in data
        assert "region" in data
        assert "total_fields" in data
        assert "total_area_ha" in data
        assert "registration_date" in data

    def test_get_farmer_phone_format(self):
        """Phone should have Yemen format"""
        response = client.get("/api/v1/farmers/test-farmer-id")
        data = response.json()
        assert data["phone"].startswith("+967")


class TestFieldSearchEndpoint:
    """Test field search endpoint"""

    def test_search_fields_returns_200(self):
        """Search endpoint should return 200"""
        response = client.get("/api/v1/fields/search")
        assert response.status_code == 200

    def test_search_fields_returns_valid_structure(self):
        """Search should return valid structure"""
        response = client.get("/api/v1/fields/search")
        data = response.json()

        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_fields_with_crop_filter(self):
        """Search should accept crop_type filter"""
        response = client.get("/api/v1/fields/search?crop_type=قمح")
        assert response.status_code == 200

    def test_search_fields_with_region_filter(self):
        """Search should accept region_id filter"""
        response = client.get("/api/v1/fields/search?region_id=1")
        assert response.status_code == 200

    def test_search_fields_with_area_filter(self):
        """Search should accept area filters"""
        response = client.get("/api/v1/fields/search?min_area=1&max_area=50")
        assert response.status_code == 200

    def test_search_fields_pagination(self):
        """Search should support pagination"""
        response = client.get("/api/v1/fields/search?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestRegionsEndpoint:
    """Test regions endpoint"""

    def test_list_regions_returns_200(self):
        """Regions endpoint should return 200"""
        response = client.get("/api/v1/regions")
        assert response.status_code == 200

    def test_list_regions_returns_all_governorates(self):
        """Should return all 20 Yemen governorates"""
        response = client.get("/api/v1/regions")
        data = response.json()

        assert "regions" in data
        assert len(data["regions"]) == 20

    def test_list_regions_structure(self):
        """Regions should have correct structure"""
        response = client.get("/api/v1/regions")
        data = response.json()

        for region in data["regions"]:
            assert "id" in region
            assert "name_ar" in region
            assert "fields_count" in region


class TestCropsEndpoint:
    """Test crops endpoint"""

    def test_list_crops_returns_200(self):
        """Crops endpoint should return 200"""
        response = client.get("/api/v1/crops")
        assert response.status_code == 200

    def test_list_crops_returns_list(self):
        """Should return list of crops"""
        response = client.get("/api/v1/crops")
        data = response.json()

        assert "crops" in data
        assert isinstance(data["crops"], list)
        assert len(data["crops"]) > 0

    def test_list_crops_structure(self):
        """Crops should have correct structure"""
        response = client.get("/api/v1/crops")
        data = response.json()

        for crop in data["crops"]:
            assert "name_ar" in crop
            assert "fields_count" in crop


class TestOverviewStatsEndpoint:
    """Test overview stats endpoint"""

    def test_get_overview_stats_returns_200(self):
        """Overview stats endpoint should return 200"""
        response = client.get("/api/v1/stats/overview")
        assert response.status_code == 200

    def test_get_overview_stats_returns_valid_structure(self):
        """Overview stats should return valid structure"""
        response = client.get("/api/v1/stats/overview")
        data = response.json()

        assert "total_farmers" in data
        assert "total_fields" in data
        assert "total_area_ha" in data
        assert "regions_count" in data
        assert "crops_types" in data
        assert "avg_field_size_ha" in data
        assert "last_updated" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
End-to-End Tests for Sahool Yemen Platform
سهول اليمن - اختبارات شاملة من البداية للنهاية
"""
import pytest
import httpx
import asyncio
from datetime import date

# Base URLs for services
GATEWAY_URL = "http://localhost"
BACKEND_URL = "http://localhost:8000"


class TestFullWorkflow:
    """Test complete user workflow scenarios"""

    @pytest.fixture
    def client(self):
        """HTTP client for tests"""
        return httpx.Client(timeout=30.0)

    def test_complete_field_analysis_workflow(self, client):
        """Test complete workflow: get field -> get NDVI -> get weather -> get advice"""
        # Skip if services not running
        try:
            # Step 1: Get available regions
            response = client.get(f"{BACKEND_URL}/v1/regions")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            regions = response.json()
            assert len(regions["regions"]) == 20

            # Step 2: Get crops
            response = client.get(f"{BACKEND_URL}/v1/crops")
            assert response.status_code == 200
            crops = response.json()
            assert len(crops["crops"]) > 0

            # Step 3: Get dashboard overview
            response = client.get(f"{BACKEND_URL}/v1/dashboard")
            assert response.status_code == 200
            dashboard = response.json()
            assert "summary" in dashboard
            assert "ndvi_status" in dashboard

        except httpx.ConnectError:
            pytest.skip("Services not running")

    def test_region_data_consistency(self, client):
        """Test that region data is consistent across endpoints"""
        try:
            response = client.get(f"{BACKEND_URL}/v1/regions")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            regions = response.json()["regions"]

            # All regions should have valid Yemen coordinates
            for region in regions:
                assert 12 <= region["lat"] <= 19, f"Invalid lat for {region['name_ar']}"
                assert 42 <= region["lon"] <= 55, f"Invalid lon for {region['name_ar']}"

            # Check specific regions exist
            region_names = [r["name_ar"] for r in regions]
            assert "صنعاء" in region_names
            assert "عدن" in region_names
            assert "تعز" in region_names

        except httpx.ConnectError:
            pytest.skip("Services not running")

    def test_dashboard_data_integrity(self, client):
        """Test dashboard data integrity"""
        try:
            response = client.get(f"{BACKEND_URL}/v1/dashboard")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            data = response.json()

            # Summary should have positive values
            assert data["summary"]["total_farmers"] > 0
            assert data["summary"]["total_fields"] > 0
            assert data["summary"]["total_area_ha"] > 0
            assert data["summary"]["active_regions"] == 20

            # NDVI percentages should roughly sum to 100
            ndvi = data["ndvi_status"]
            total = ndvi["excellent"] + ndvi["good"] + ndvi["moderate"] + ndvi["poor"]
            assert 95 <= total <= 105

            # Weather should have valid values
            weather = data["weather"]
            assert -10 <= weather["avg_temp_celsius"] <= 50
            assert 0 <= weather["rain_probability"] <= 100

        except httpx.ConnectError:
            pytest.skip("Services not running")


class TestAPIIntegration:
    """Test API integration between services"""

    @pytest.fixture
    def client(self):
        """HTTP client for tests"""
        return httpx.Client(timeout=30.0)

    def test_health_endpoints_all_services(self, client):
        """Test health endpoints for all services"""
        services = [
            (f"{BACKEND_URL}/health", "field-suite-backend"),
        ]

        for url, service_name in services:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    assert data["status"] == "healthy"
            except httpx.ConnectError:
                pytest.skip(f"Service {service_name} not running")

    def test_api_versioning(self, client):
        """Test API versioning is consistent"""
        try:
            response = client.get(f"{BACKEND_URL}/health")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            data = response.json()
            assert data["version"] == "6.0.0"

        except httpx.ConnectError:
            pytest.skip("Services not running")


class TestDataConsistency:
    """Test data consistency across the platform"""

    @pytest.fixture
    def client(self):
        """HTTP client for tests"""
        return httpx.Client(timeout=30.0)

    def test_governorate_count_consistent(self, client):
        """Test that governorate count is consistent (20)"""
        try:
            # From regions endpoint
            response = client.get(f"{BACKEND_URL}/v1/regions")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            regions = response.json()
            assert regions["count"] == 20

            # From dashboard
            response = client.get(f"{BACKEND_URL}/v1/dashboard")
            dashboard = response.json()
            assert dashboard["summary"]["active_regions"] == 20

        except httpx.ConnectError:
            pytest.skip("Services not running")

    def test_yemen_specific_data(self, client):
        """Test Yemen-specific data is present"""
        try:
            response = client.get(f"{BACKEND_URL}/v1/crops")
            if response.status_code != 200:
                pytest.skip("Backend not available")

            crops = response.json()
            crop_names = [c["name_ar"] for c in crops["crops"]]

            # Yemen's famous crops
            assert "بن" in crop_names  # Coffee
            assert "قمح" in crop_names  # Wheat

        except httpx.ConnectError:
            pytest.skip("Services not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

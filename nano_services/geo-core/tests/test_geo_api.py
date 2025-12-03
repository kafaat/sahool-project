"""
Unit tests for Geo Core Service
سهول اليمن - اختبارات خدمة المساحات الجغرافية
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
        assert data["service"] == "geo-core"


class TestComputeAreaEndpoint:
    """Test area computation endpoint"""

    @pytest.fixture
    def sample_polygon(self):
        """Sample polygon geometry"""
        return {
            "type": "Polygon",
            "coordinates": [[
                [44.20, 15.35],
                [44.21, 15.35],
                [44.21, 15.36],
                [44.20, 15.36],
                [44.20, 15.35]
            ]]
        }

    def test_compute_area_returns_200(self, sample_polygon):
        """Compute area endpoint should return 200"""
        response = client.post("/api/v1/geo/compute-area", json=sample_polygon)
        assert response.status_code == 200

    def test_compute_area_returns_valid_structure(self, sample_polygon):
        """Compute area should return valid structure"""
        response = client.post("/api/v1/geo/compute-area", json=sample_polygon)
        data = response.json()

        assert "area_ha" in data
        assert "area_m2" in data
        assert "perimeter_m" in data
        assert "centroid_lat" in data
        assert "centroid_lon" in data
        assert "bounding_box" in data

    def test_compute_area_positive_values(self, sample_polygon):
        """Area values should be positive"""
        response = client.post("/api/v1/geo/compute-area", json=sample_polygon)
        data = response.json()

        assert data["area_ha"] > 0
        assert data["area_m2"] > 0
        assert data["perimeter_m"] > 0

    def test_compute_area_consistent_units(self, sample_polygon):
        """Area in m2 should equal ha * 10000"""
        response = client.post("/api/v1/geo/compute-area", json=sample_polygon)
        data = response.json()

        expected_m2 = data["area_ha"] * 10000
        assert abs(data["area_m2"] - expected_m2) < 1  # Allow 1 m2 tolerance

    def test_compute_area_bounding_box_valid(self, sample_polygon):
        """Bounding box should have valid structure"""
        response = client.post("/api/v1/geo/compute-area", json=sample_polygon)
        data = response.json()

        bbox = data["bounding_box"]
        assert "min_lat" in bbox
        assert "max_lat" in bbox
        assert "min_lon" in bbox
        assert "max_lon" in bbox
        assert bbox["min_lat"] <= bbox["max_lat"]
        assert bbox["min_lon"] <= bbox["max_lon"]

    def test_compute_area_invalid_polygon_returns_error(self):
        """Invalid polygon should return error"""
        invalid_polygon = {"coordinates": [[1, 2]]}  # Too few points
        response = client.post("/api/v1/geo/compute-area", json=invalid_polygon)
        assert response.status_code in [400, 422]


class TestElevationEndpoint:
    """Test elevation endpoint"""

    def test_get_elevation_returns_200(self):
        """Elevation endpoint should return 200"""
        response = client.get("/api/v1/geo/elevation?lat=15.35&lon=44.20")
        assert response.status_code == 200

    def test_get_elevation_returns_valid_structure(self):
        """Elevation should return valid structure"""
        response = client.get("/api/v1/geo/elevation?lat=15.35&lon=44.20")
        data = response.json()

        assert "lat" in data
        assert "lon" in data
        assert "elevation_m" in data
        assert "slope_percent" in data
        assert "aspect_degrees" in data

    def test_get_elevation_coordinates_match(self):
        """Returned coordinates should match request"""
        lat, lon = 15.35, 44.20
        response = client.get(f"/api/v1/geo/elevation?lat={lat}&lon={lon}")
        data = response.json()

        assert data["lat"] == lat
        assert data["lon"] == lon

    def test_get_elevation_outside_yemen_returns_error(self):
        """Coordinates outside Yemen should return error"""
        # Coordinates outside Yemen bounds
        response = client.get("/api/v1/geo/elevation?lat=50.0&lon=44.20")
        assert response.status_code == 400

    def test_get_elevation_slope_valid_range(self):
        """Slope should be non-negative"""
        response = client.get("/api/v1/geo/elevation?lat=15.35&lon=44.20")
        data = response.json()
        assert data["slope_percent"] >= 0

    def test_get_elevation_aspect_valid_range(self):
        """Aspect should be between 0 and 360"""
        response = client.get("/api/v1/geo/elevation?lat=15.35&lon=44.20")
        data = response.json()
        assert 0 <= data["aspect_degrees"] <= 360


class TestDistanceEndpoint:
    """Test distance calculation endpoint"""

    def test_calculate_distance_returns_200(self):
        """Distance endpoint should return 200"""
        response = client.get(
            "/api/v1/geo/distance?lat1=15.35&lon1=44.20&lat2=15.40&lon2=44.25"
        )
        assert response.status_code == 200

    def test_calculate_distance_returns_valid_structure(self):
        """Distance should return valid structure"""
        response = client.get(
            "/api/v1/geo/distance?lat1=15.35&lon1=44.20&lat2=15.40&lon2=44.25"
        )
        data = response.json()

        assert "distance_km" in data
        assert "distance_m" in data
        assert "bearing_degrees" in data

    def test_calculate_distance_consistent_units(self):
        """Distance in m should equal km * 1000"""
        response = client.get(
            "/api/v1/geo/distance?lat1=15.35&lon1=44.20&lat2=15.40&lon2=44.25"
        )
        data = response.json()

        expected_m = data["distance_km"] * 1000
        assert abs(data["distance_m"] - expected_m) < 1  # Allow 1m tolerance

    def test_calculate_distance_same_point_returns_zero(self):
        """Same point should return zero distance"""
        response = client.get(
            "/api/v1/geo/distance?lat1=15.35&lon1=44.20&lat2=15.35&lon2=44.20"
        )
        data = response.json()
        assert data["distance_km"] < 0.001

    def test_calculate_distance_bearing_valid_range(self):
        """Bearing should be between 0 and 360"""
        response = client.get(
            "/api/v1/geo/distance?lat1=15.35&lon1=44.20&lat2=15.40&lon2=44.25"
        )
        data = response.json()
        assert 0 <= data["bearing_degrees"] <= 360


class TestZoneInfoEndpoint:
    """Test zone info endpoint"""

    def test_get_zone_info_returns_200(self):
        """Zone info endpoint should return 200"""
        response = client.get("/api/v1/geo/zone-info?lat=15.35&lon=44.20")
        assert response.status_code == 200

    def test_get_zone_info_returns_valid_structure(self):
        """Zone info should return valid structure"""
        response = client.get("/api/v1/geo/zone-info?lat=15.35&lon=44.20")
        data = response.json()

        assert "zone_name" in data
        assert "zone_type" in data
        assert "agricultural_suitability" in data
        assert "water_availability" in data
        assert "soil_quality" in data


class TestValidateGeometryEndpoint:
    """Test geometry validation endpoint"""

    def test_validate_point_returns_valid(self):
        """Valid point should pass validation"""
        geometry = {"type": "Point", "coordinates": [44.20, 15.35]}
        response = client.post("/api/v1/geo/validate", json=geometry)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_polygon_returns_valid(self):
        """Valid polygon should pass validation"""
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [44.20, 15.35],
                [44.21, 15.35],
                [44.21, 15.36],
                [44.20, 15.36],
                [44.20, 15.35]
            ]]
        }
        response = client.post("/api/v1/geo/validate", json=geometry)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_type_returns_errors(self):
        """Invalid geometry type should fail validation"""
        geometry = {"type": "InvalidType", "coordinates": []}
        response = client.post("/api/v1/geo/validate", json=geometry)
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

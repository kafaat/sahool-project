"""
Comprehensive tests for Field Suite Backend
Including CRUD, validation, security, and rate limiting tests
"""
import pytest
from fastapi.testclient import TestClient
from main import app, FIELDS_DB, rate_limiter, settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear database and rate limiter before each test"""
    FIELDS_DB.clear()
    rate_limiter.clients.clear()
    yield
    FIELDS_DB.clear()
    rate_limiter.clients.clear()


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthCheck:
    def test_health_check(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Field Suite" in data["service"]

    def test_health_check_has_version(self):
        response = client.get("/")
        data = response.json()
        assert "version" in data
        assert data["version"] is not None

    def test_health_check_has_capabilities(self):
        response = client.get("/")
        data = response.json()
        assert "capabilities" in data
        assert "rate_limiting" in data["capabilities"]

    def test_health_check_has_uptime(self):
        response = client.get("/")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_readiness_probe(self):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_probe(self):
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


# =============================================================================
# Field CRUD Tests
# =============================================================================

class TestFieldsCRUD:
    def test_list_fields_empty(self):
        response = client.get("/fields/")
        assert response.status_code == 200
        data = response.json()
        assert data["fields"] == []
        assert data["count"] == 0

    def test_create_field(self):
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Field"
        assert data["geometryType"] == "Polygon"
        assert data["id"] is not None
        assert data["metadata"]["createdAt"] is not None

    def test_create_field_with_metadata(self):
        field_data = {
            "name": "Field with Metadata",
            "geometryType": "Rectangle",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]],
            "metadata": {
                "source": "manual",
                "cropType": "wheat",
                "notes": "Test notes"
            }
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["source"] == "manual"
        assert data["metadata"]["cropType"] == "wheat"

    def test_get_field(self):
        # Create a field first
        field_data = {
            "name": "Get Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        create_response = client.post("/fields/", json=field_data)
        field_id = create_response.json()["id"]

        # Get the field
        response = client.get(f"/fields/{field_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Field"

    def test_get_field_not_found(self):
        response = client.get("/fields/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_field(self):
        # Create a field
        field_data = {
            "name": "Original Name",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        create_response = client.post("/fields/", json=field_data)
        field_id = create_response.json()["id"]

        # Update the field
        updated_data = {
            "name": "Updated Name",
            "geometryType": "Rectangle",
            "coordinates": [[[46.0, 16.0], [46.1, 16.0], [46.1, 16.1], [46.0, 16.0]]]
        }
        response = client.put(f"/fields/{field_id}", json=updated_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_preserves_created_at(self):
        # Create a field
        field_data = {
            "name": "Original",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        create_response = client.post("/fields/", json=field_data)
        field_id = create_response.json()["id"]
        created_at = create_response.json()["metadata"]["createdAt"]

        # Update the field
        updated_data = {
            "name": "Updated",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.put(f"/fields/{field_id}", json=updated_data)
        assert response.json()["metadata"]["createdAt"] == created_at

    def test_delete_field(self):
        # Create a field
        field_data = {
            "name": "To Delete",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        create_response = client.post("/fields/", json=field_data)
        field_id = create_response.json()["id"]

        # Delete the field
        response = client.delete(f"/fields/{field_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/fields/{field_id}")
        assert get_response.status_code == 404

    def test_list_fields_with_data(self):
        # Create multiple fields
        for i in range(3):
            field_data = {
                "name": f"Field {i}",
                "geometryType": "Polygon",
                "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
            }
            client.post("/fields/", json=field_data)

        response = client.get("/fields/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["fields"]) == 3


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    def test_invalid_coordinates_empty(self):
        field_data = {
            "name": "Invalid Field",
            "geometryType": "Polygon",
            "coordinates": []
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_invalid_coordinates_out_of_range_longitude(self):
        field_data = {
            "name": "Invalid Coords",
            "geometryType": "Polygon",
            "coordinates": [[[200.0, 15.0], [45.1, 15.0], [45.1, 15.1], [200.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_invalid_coordinates_out_of_range_latitude(self):
        field_data = {
            "name": "Invalid Coords",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 100.0], [45.1, 15.0], [45.1, 15.1], [45.0, 100.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_invalid_geometry_type(self):
        field_data = {
            "name": "Invalid Type",
            "geometryType": "InvalidType",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_empty_name(self):
        field_data = {
            "name": "",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_name_too_long(self):
        field_data = {
            "name": "A" * 300,  # Exceeds 255 char limit
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_invalid_center_coordinates(self):
        field_data = {
            "name": "Invalid Center",
            "geometryType": "Circle",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]],
            "center": [200.0, 15.0]  # Invalid longitude
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_negative_radius(self):
        field_data = {
            "name": "Invalid Radius",
            "geometryType": "Circle",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]],
            "center": [45.0, 15.0],
            "radiusMeters": -100  # Negative radius
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422


# =============================================================================
# Auto-Detect Tests
# =============================================================================

class TestAutoDetect:
    def test_auto_detect_mock(self):
        response = client.post("/fields/auto-detect", json={"mock": True})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["fields"]) == 1
        assert data["fields"][0]["metadata"]["source"] == "auto_ndvi"

    def test_auto_detect_saves_to_db(self):
        response = client.post("/fields/auto-detect", json={"mock": True})
        field_id = response.json()["fields"][0]["id"]

        # Verify field exists in DB
        get_response = client.get(f"/fields/{field_id}")
        assert get_response.status_code == 200


# =============================================================================
# Zone Split Tests
# =============================================================================

class TestZones:
    def test_split_into_zones(self):
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        request_data = {
            "field": field_data,
            "zones": 3
        }
        response = client.post("/fields/zones", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["fields"]) == 3
        for i, zone in enumerate(data["fields"]):
            assert f"Zone {i+1}" in zone["name"]

    def test_split_zones_too_many(self):
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        request_data = {
            "field": field_data,
            "zones": 25  # Exceeds max of 20
        }
        response = client.post("/fields/zones", json=request_data)
        assert response.status_code == 422

    def test_split_zones_too_few(self):
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        request_data = {
            "field": field_data,
            "zones": 0  # Below min of 1
        }
        response = client.post("/fields/zones", json=request_data)
        assert response.status_code == 422


# =============================================================================
# Security Tests
# =============================================================================

class TestSecurity:
    def test_response_has_request_id_header(self):
        """Test that responses include X-Request-ID header"""
        response = client.get("/")
        assert "x-request-id" in response.headers

    def test_response_has_process_time_header(self):
        """Test that responses include X-Process-Time header"""
        response = client.get("/")
        assert "x-process-time" in response.headers

    def test_response_has_rate_limit_header(self):
        """Test that responses include rate limit header"""
        response = client.get("/")
        assert "x-ratelimit-remaining" in response.headers

    def test_custom_request_id_preserved(self):
        """Test that custom X-Request-ID is preserved"""
        response = client.get("/", headers={"X-Request-ID": "test-123"})
        assert response.headers.get("x-request-id") == "test-123"

    def test_sql_injection_in_field_id(self):
        """Test SQL injection attempt in field ID"""
        response = client.get("/fields/'; DROP TABLE fields;--")
        assert response.status_code == 404  # Should be 404, not 500

    def test_xss_in_field_name(self):
        """Test XSS attempt in field name is stored safely"""
        field_data = {
            "name": "<script>alert('xss')</script>",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 201
        # Name should be stored as-is (escaping is frontend responsibility)
        assert response.json()["name"] == "<script>alert('xss')</script>"

    def test_large_payload_rejection(self):
        """Test that extremely large payloads are handled"""
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[float(i), float(i)] for i in range(10000)]]  # Large coordinate list
        }
        response = client.post("/fields/", json=field_data)
        # Should either accept or return validation error, not crash
        assert response.status_code in [201, 422]


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestRateLimiting:
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows normal requests"""
        response = client.get("/fields/")
        assert response.status_code == 200

    def test_rate_limit_remaining_decreases(self):
        """Test that rate limit remaining decreases"""
        response1 = client.get("/fields/")
        remaining1 = int(response1.headers.get("x-ratelimit-remaining", 100))

        response2 = client.get("/fields/")
        remaining2 = int(response2.headers.get("x-ratelimit-remaining", 100))

        assert remaining2 < remaining1


# =============================================================================
# AG-UI Protocol Tests
# =============================================================================

class TestAGUIProtocol:
    def test_agui_state_endpoint(self):
        """Test AG-UI state endpoint"""
        response = client.get("/api/copilotkit/state")
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        assert "fieldsCount" in data
        assert "lastUpdated" in data

    def test_agui_state_reflects_db(self):
        """Test AG-UI state reflects database"""
        # Create a field
        field_data = {
            "name": "AG-UI Test",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        client.post("/fields/", json=field_data)

        # Check state
        response = client.get("/api/copilotkit/state")
        data = response.json()
        assert data["fieldsCount"] == 1

    def test_copilotkit_endpoint_returns_stream(self):
        """Test CopilotKit endpoint returns SSE stream"""
        response = client.post(
            "/api/copilotkit",
            json={"messages": [{"role": "user", "content": "hello"}]}
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    def test_404_error_format(self):
        """Test 404 error response format"""
        response = client.get("/fields/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "timestamp" in data
        assert "path" in data

    def test_422_validation_error(self):
        """Test 422 validation error"""
        response = client.post("/fields/", json={"invalid": "data"})
        assert response.status_code == 422

    def test_method_not_allowed(self):
        """Test method not allowed"""
        response = client.patch("/fields/test-id", json={})
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

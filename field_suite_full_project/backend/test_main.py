import pytest
from fastapi.testclient import TestClient
from main import app, FIELDS_DB

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    FIELDS_DB.clear()
    yield
    FIELDS_DB.clear()


class TestHealthCheck:
    def test_health_check(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Field Suite Backend"


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


class TestValidation:
    def test_invalid_coordinates_empty(self):
        field_data = {
            "name": "Invalid Field",
            "geometryType": "Polygon",
            "coordinates": []
        }
        response = client.post("/fields/", json=field_data)
        assert response.status_code == 422

    def test_invalid_coordinates_out_of_range(self):
        field_data = {
            "name": "Invalid Coords",
            "geometryType": "Polygon",
            "coordinates": [[[200.0, 15.0], [45.1, 15.0], [45.1, 15.1], [200.0, 15.0]]]
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


class TestAutoDetect:
    def test_auto_detect_mock(self):
        response = client.post("/fields/auto-detect", json={"mock": True})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["fields"]) == 1
        assert data["fields"][0]["metadata"]["source"] == "auto_ndvi"


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

    def test_split_zones_validation(self):
        field_data = {
            "name": "Test Field",
            "geometryType": "Polygon",
            "coordinates": [[[45.0, 15.0], [45.1, 15.0], [45.1, 15.1], [45.0, 15.0]]]
        }
        # Test invalid zone count (too high)
        request_data = {
            "field": field_data,
            "zones": 25
        }
        response = client.post("/fields/zones", json=request_data)
        assert response.status_code == 422

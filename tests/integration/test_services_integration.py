"""
Integration Tests for Sahool Yemen Services
اختبارات التكامل لخدمات سهول اليمن
"""

import os
import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# Get the project root directory dynamically
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWeatherServiceIntegration:
    """Integration tests for Weather Core service."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_weather_health_endpoint(self):
        """Test weather service health endpoint."""
        from fastapi.testclient import TestClient

        # Import dynamically to avoid import errors
        import sys
        weather_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'weather-core')
        if weather_core_path not in sys.path:
            sys.path.insert(0, weather_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Weather service not available")

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "weather-core"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_weather_region_endpoint(self):
        """Test getting weather by region."""
        from fastapi.testclient import TestClient

        import sys
        weather_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'weather-core')
        if weather_core_path not in sys.path:
            sys.path.insert(0, weather_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Weather service not available")

        client = TestClient(app)
        response = client.get("/api/v1/weather/regions/1")

        assert response.status_code == 200
        data = response.json()
        assert "temperature" in data
        assert "humidity" in data
        assert data["region_id"] == 1

    @pytest.mark.asyncio
    async def test_weather_forecast_endpoint(self):
        """Test weather forecast endpoint."""
        from fastapi.testclient import TestClient

        import sys
        weather_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'weather-core')
        if weather_core_path not in sys.path:
            sys.path.insert(0, weather_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Weather service not available")

        client = TestClient(app)
        response = client.get("/api/v1/weather/regions/1/forecast?days=5")

        assert response.status_code == 200
        data = response.json()
        assert "forecasts" in data
        assert len(data["forecasts"]) == 5

    @pytest.mark.asyncio
    async def test_weather_alerts_endpoint(self):
        """Test weather alerts endpoint."""
        from fastapi.testclient import TestClient

        import sys
        weather_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'weather-core')
        if weather_core_path not in sys.path:
            sys.path.insert(0, weather_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Weather service not available")

        client = TestClient(app)
        response = client.get("/api/v1/weather/alerts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGeoServiceIntegration:
    """Integration tests for Geo Core service."""

    @pytest.mark.asyncio
    async def test_geo_health_endpoint(self):
        """Test geo service health endpoint."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "geo-core"

    @pytest.mark.asyncio
    async def test_geo_compute_area(self):
        """Test area computation."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)

        # Simple polygon in Yemen coordinates
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [44.0, 15.0],
                [44.1, 15.0],
                [44.1, 15.1],
                [44.0, 15.1],
                [44.0, 15.0]
            ]]
        }

        response = client.post("/api/v1/geo/compute-area", json=geometry)

        assert response.status_code == 200
        data = response.json()
        assert "area_ha" in data
        assert "area_m2" in data
        assert "perimeter_m" in data
        assert data["area_ha"] > 0

    @pytest.mark.asyncio
    async def test_geo_elevation(self):
        """Test elevation endpoint."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)
        response = client.get("/api/v1/geo/elevation?lat=15.3&lon=44.2")

        assert response.status_code == 200
        data = response.json()
        assert "elevation_m" in data
        assert "slope_percent" in data
        assert "terrain_type" in data

    @pytest.mark.asyncio
    async def test_geo_distance(self):
        """Test distance calculation."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)
        response = client.get(
            "/api/v1/geo/distance?lat1=15.3&lon1=44.2&lat2=13.5&lon2=44.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert "distance_km" in data
        assert "distance_m" in data
        assert "bearing_degrees" in data
        assert data["distance_km"] > 0

    @pytest.mark.asyncio
    async def test_geo_zone_info(self):
        """Test zone info endpoint."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)
        response = client.get("/api/v1/geo/zone-info?lat=15.3&lon=44.2")

        assert response.status_code == 200
        data = response.json()
        assert "zone_name" in data
        assert "zone_type" in data
        assert "recommended_crops" in data

    @pytest.mark.asyncio
    async def test_geo_validate_geometry(self):
        """Test geometry validation."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)

        # Valid point
        geometry = {"type": "Point", "coordinates": [44.2, 15.3]}
        response = client.post("/api/v1/geo/validate", json=geometry)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_geo_validate_invalid_geometry(self):
        """Test invalid geometry validation."""
        from fastapi.testclient import TestClient

        import sys
        geo_core_path = os.path.join(PROJECT_ROOT, 'nano_services', 'geo-core')
        if geo_core_path not in sys.path:
            sys.path.insert(0, geo_core_path)

        try:
            from app.main import app
        except ImportError:
            pytest.skip("Geo service not available")

        client = TestClient(app)

        # Invalid - outside Yemen
        geometry = {"type": "Point", "coordinates": [0, 0]}
        response = client.post("/api/v1/geo/validate", json=geometry)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_database_manager_creation(self):
        """Test DatabaseManager can be instantiated."""
        try:
            from sahool_shared.database import DatabaseManager

            manager = DatabaseManager(
                database_url="postgresql://test:test@localhost:5432/test"
            )
            assert manager is not None
            assert "postgresql://" in manager.database_url
        except ImportError:
            pytest.skip("Shared library not available")

    @pytest.mark.asyncio
    async def test_model_imports(self):
        """Test ORM models can be imported."""
        try:
            from sahool_shared.models import (
                Field, Region, Farmer, WeatherData, NDVIResult,
                SoilAnalysis, YieldRecord, IrrigationSchedule,
                PlantHealth, AuditLog
            )

            # All models should be importable
            assert Field is not None
            assert Region is not None
            assert SoilAnalysis is not None
        except ImportError:
            pytest.skip("Shared library not available")


class TestAuthIntegration:
    """Integration tests for authentication."""

    @pytest.mark.asyncio
    async def test_jwt_token_creation(self):
        """Test JWT token creation."""
        try:
            from sahool_shared.auth import create_access_token, verify_token

            token = create_access_token(
                user_id="test-user",
                tenant_id="test-tenant",
                role="admin"
            )

            assert token is not None
            assert len(token) > 0

            # Verify the token
            payload = verify_token(token)
            assert payload.sub == "test-user"
            assert payload.tenant_id == "test-tenant"
            assert payload.role == "admin"
        except ImportError:
            pytest.skip("Shared library not available")

    @pytest.mark.asyncio
    async def test_jwt_token_pair(self):
        """Test JWT token pair creation."""
        try:
            from sahool_shared.auth.jwt import JWTHandler

            handler = JWTHandler(secret_key="test-secret")
            tokens = handler.create_token_pair(
                user_id="user-1",
                tenant_id="tenant-1",
                role="user"
            )

            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert tokens["token_type"] == "bearer"
        except ImportError:
            pytest.skip("Shared library not available")


class TestEventBusIntegration:
    """Integration tests for event bus."""

    @pytest.mark.asyncio
    async def test_in_memory_event_bus(self):
        """Test in-memory event bus."""
        try:
            from sahool_shared.events import InMemoryEventBus, Event

            bus = InMemoryEventBus()
            received_events = []

            async def handler(event: Event):
                received_events.append(event)

            await bus.subscribe("test.event", handler)

            event = Event(type="test.event", data={"test": "data"})
            await bus.publish(event)

            assert len(received_events) == 1
            assert received_events[0].type == "test.event"
        except ImportError:
            pytest.skip("Shared library not available")

    @pytest.mark.asyncio
    async def test_field_created_event(self):
        """Test FieldCreatedEvent."""
        try:
            from sahool_shared.events import FieldCreatedEvent

            event = FieldCreatedEvent.create(
                field_id="field-1",
                farmer_id="farmer-1",
                tenant_id="tenant-1",
                name="حقل القمح",
                area_hectares=5.5,
                crop_type="قمح"
            )

            assert event.type == "field.created"
            assert event.data["name"] == "حقل القمح"
            assert event.data["area_hectares"] == 5.5
        except ImportError:
            pytest.skip("Shared library not available")

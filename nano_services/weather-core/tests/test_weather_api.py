"""
Unit tests for Weather Core Service
سهول اليمن - اختبارات خدمة الطقس
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
        assert data["service"] == "weather-core"

    def test_health_check_includes_region(self):
        """Health endpoint should include Yemen region"""
        response = client.get("/health")
        data = response.json()
        assert data["region"] == "Yemen"


class TestWeatherEndpoint:
    """Test weather data endpoint"""

    def test_get_weather_returns_200(self):
        """Weather endpoint should return 200 for valid field_id"""
        response = client.get("/api/v1/weather/fields/1")
        assert response.status_code == 200

    def test_get_weather_returns_valid_structure(self):
        """Weather endpoint should return valid data structure"""
        response = client.get("/api/v1/weather/fields/1")
        data = response.json()

        assert "field_id" in data
        assert "date" in data
        assert "tmax" in data
        assert "tmin" in data
        assert "tmean" in data
        assert "rain_mm" in data
        assert "humidity" in data
        assert "wind_speed" in data

    def test_get_weather_field_id_matches(self):
        """Weather endpoint should return correct field_id"""
        field_id = 42
        response = client.get(f"/api/v1/weather/fields/{field_id}")
        data = response.json()
        assert data["field_id"] == field_id

    def test_get_weather_with_target_date(self):
        """Weather endpoint should accept target_date parameter"""
        target_date = "2024-06-15"
        response = client.get(f"/api/v1/weather/fields/1?target_date={target_date}")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == target_date

    def test_get_weather_temperature_range_valid(self):
        """Temperature values should be within realistic range"""
        response = client.get("/api/v1/weather/fields/1")
        data = response.json()

        assert -10 <= data["tmin"] <= 50
        assert -10 <= data["tmax"] <= 60
        assert data["tmin"] <= data["tmax"]

    def test_get_weather_humidity_range_valid(self):
        """Humidity should be between 0 and 100"""
        response = client.get("/api/v1/weather/fields/1")
        data = response.json()
        assert 0 <= data["humidity"] <= 100

    def test_get_weather_rain_non_negative(self):
        """Rain amount should be non-negative"""
        response = client.get("/api/v1/weather/fields/1")
        data = response.json()
        assert data["rain_mm"] >= 0

    def test_get_weather_region_type_highland(self):
        """Weather endpoint should accept region_type parameter"""
        response = client.get("/api/v1/weather/fields/1?region_type=highland")
        assert response.status_code == 200

    def test_get_weather_region_type_coastal(self):
        """Weather endpoint should work with coastal region type"""
        response = client.get("/api/v1/weather/fields/1?region_type=coastal")
        assert response.status_code == 200


class TestWeatherForecastEndpoint:
    """Test weather forecast endpoint"""

    def test_get_forecast_returns_200(self):
        """Forecast endpoint should return 200"""
        response = client.get("/api/v1/weather/fields/1/forecast")
        assert response.status_code == 200

    def test_get_forecast_returns_valid_structure(self):
        """Forecast endpoint should return valid structure"""
        response = client.get("/api/v1/weather/fields/1/forecast")
        data = response.json()

        assert "field_id" in data
        assert "forecasts" in data
        assert isinstance(data["forecasts"], list)

    def test_get_forecast_default_days(self):
        """Forecast should return 7 days by default"""
        response = client.get("/api/v1/weather/fields/1/forecast")
        data = response.json()
        assert len(data["forecasts"]) == 7

    def test_get_forecast_custom_days(self):
        """Forecast should accept custom days parameter"""
        days = 5
        response = client.get(f"/api/v1/weather/fields/1/forecast?days={days}")
        data = response.json()
        assert len(data["forecasts"]) == days

    def test_get_forecast_item_structure(self):
        """Forecast items should have correct structure"""
        response = client.get("/api/v1/weather/fields/1/forecast")
        data = response.json()

        for forecast in data["forecasts"]:
            assert "date" in forecast
            assert "tmax" in forecast
            assert "tmin" in forecast
            assert "rain_probability" in forecast
            assert "description_ar" in forecast


class TestWeatherAlertsEndpoint:
    """Test weather alerts endpoint"""

    def test_get_alerts_returns_200(self):
        """Alerts endpoint should return 200"""
        response = client.get("/api/v1/weather/alerts")
        assert response.status_code == 200

    def test_get_alerts_returns_list(self):
        """Alerts endpoint should return list of alerts"""
        response = client.get("/api/v1/weather/alerts")
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_alerts_with_region_filter(self):
        """Alerts endpoint should accept region_id filter"""
        response = client.get("/api/v1/weather/alerts?region_id=1")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

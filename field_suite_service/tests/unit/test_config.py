"""
Unit tests for Configuration Module
سهول اليمن - اختبارات وحدة الإعدادات
"""
import pytest
import os


class TestSettingsConfiguration:
    """Test settings configuration"""

    def test_settings_loads_successfully(self):
        """Settings should load without errors"""
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

        from app.core.config import Settings
        settings = Settings()
        assert settings is not None

    def test_settings_default_values(self):
        """Settings should have correct default values"""
        from app.core.config import Settings
        settings = Settings()

        assert settings.SERVICE_NAME == "field-suite-ndvi-advisor"
        assert settings.VERSION == "6.0.0"
        assert settings.DEFAULT_LAT == 15.3547  # Sana'a
        assert settings.DEFAULT_LON == 44.2067
        assert settings.TIMEZONE == "Asia/Aden"
        assert settings.CURRENCY == "YER"
        assert settings.LANGUAGE == "ar-YE"

    def test_settings_cache_ttl_defaults(self):
        """Cache TTL should have correct defaults"""
        from app.core.config import Settings
        settings = Settings()

        assert settings.CACHE_TTL == 300
        assert settings.LLM_CACHE_TTL == 3600

    def test_settings_jwt_defaults(self):
        """JWT settings should have correct defaults"""
        from app.core.config import Settings
        settings = Settings()

        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_EXPIRE_MINUTES == 60

    def test_get_settings_returns_cached(self):
        """get_settings should return cached instance"""
        from app.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

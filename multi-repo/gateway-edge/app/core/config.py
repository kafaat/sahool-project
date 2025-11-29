# app/core/config.py
"""
Application settings module.

- Compatible with pydantic v2 using the `pydantic-settings` package.
- Exports a module-level `settings` instance so other modules can:
    from app.core.config import settings
- Provides `get_settings()` for FastAPI dependency injection (cached).
"""

from functools import lru_cache
from typing import Dict, Optional

# Use pydantic-settings BaseSettings (you already have it in your environment)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 9000

    PLATFORM_URL: str = "http://platform-core:9000"
    GEO_URL: str = "http://geo-core:8005"
    IMAGERY_URL: str = "http://imagery-core:8006"
    SOIL_URL: str = "http://soil-core:8002"
    WEATHER_URL: str = "http://weather-core:8003"
    ALERTS_URL: str = "http://alerts-core:8004"
    ANALYTICS_URL: str = "http://analytics-core:8005"
    AGENT_URL: str = "http://agent-ai:9010"

    # بسيط: API key ثابت للتجارب، يمكن ربطه لاحقاً بجدول في platform-core
    API_KEYS: Dict[str, str] = {
        "dev-key": "dev-tenant"  # key -> label فقط
    }
    AUTH_ENABLED: bool = False  # يمكن تفعيلها في الإنتاج

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Factory for dependency injection (FastAPI). Cached so same instance is reused."""
    return Settings()


# Module-level settings instance for direct imports:
settings: Settings = get_settings()

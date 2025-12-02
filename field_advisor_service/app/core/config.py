"""
Configuration settings for Field Advisor Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Service Info
    service_name: str = "field-advisor-service"
    service_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/field_advisor"

    # External Services
    ndvi_service_url: str = "http://localhost:8000"
    weather_api_url: str = "https://api.open-meteo.com/v1"
    weather_api_key: str = ""

    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  # 5 minutes

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Advisor Settings
    default_analysis_days: int = 30
    ndvi_critical_threshold: float = 0.3
    ndvi_warning_threshold: float = 0.4
    ndvi_healthy_threshold: float = 0.6

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

"""
سهول اليمن - Configuration Settings
إعدادات التكوين للمنصة
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Service Info
    SERVICE_NAME: str = "field-suite-ndvi-advisor"
    VERSION: str = "6.0.0"
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")

    # External Services
    IMAGERY_CORE_BASE_URL: str = Field(
        default="http://imagery-core:8000",
        env="IMAGERY_CORE_BASE_URL"
    )
    ANALYTICS_CORE_BASE_URL: str = Field(
        default="http://analytics-core:8000",
        env="ANALYTICS_CORE_BASE_URL"
    )
    GEO_CORE_BASE_URL: str = Field(
        default="http://geo-core:8000",
        env="GEO_CORE_BASE_URL"
    )
    WEATHER_CORE_BASE_URL: str = Field(
        default="http://weather-core:8000",
        env="WEATHER_CORE_BASE_URL"
    )
    ADVISOR_CORE_BASE_URL: str = Field(
        default="http://advisor-core:8000",
        env="ADVISOR_CORE_BASE_URL"
    )
    QUERY_CORE_BASE_URL: str = Field(
        default="http://query-core:8000",
        env="QUERY_CORE_BASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    CACHE_TTL: int = 300
    LLM_CACHE_TTL: int = 3600

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost:5432/db",
        env="DATABASE_URL"
    )

    # Timeouts
    REQUEST_TIMEOUT: int = 30

    # LLM
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = "/app/logs/sahool.log"

    # Security
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    API_KEY_SECRET: str = Field(
        default="change-me-in-production",
        env="API_KEY_SECRET"
    )

    # Metrics
    METRICS_PORT: int = 8001
    METRICS_ENABLED: bool = True

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    API_RATE_LIMIT: int = 200
    API_BURST: int = 20

    # Yemen-specific settings
    DEFAULT_LAT: float = 15.3547  # Sana'a
    DEFAULT_LON: float = 44.2067
    TIMEZONE: str = "Asia/Aden"
    CURRENCY: str = "YER"
    LANGUAGE: str = "ar-YE"

    # File Storage
    MAX_UPLOAD_SIZE: str = "50MB"
    STATIC_FILES_PATH: str = "/app/static"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v and not v.startswith(("postgresql://", "postgres://")):
            # Allow empty or default for development
            if v != "postgresql://user:pass@localhost:5432/db":
                raise ValueError("Invalid DATABASE_URL format")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

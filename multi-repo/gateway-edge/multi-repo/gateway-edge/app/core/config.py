
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    PORT: int = 9000
    SERVICES_BASE: str = "http://localhost"

    PLATFORM_URL: str = "http://localhost:8000"
    GEO_URL: str = "http://localhost:8001"
    IMAGERY_URL: str = "http://localhost:8002"
    SOIL_URL: str = "http://localhost:8002"
    WEATHER_URL: str = "http://localhost:8003"
    ALERTS_URL: str = "http://localhost:8004"
    ANALYTICS_URL: str = "http://localhost:8005"
    TIMELINE_URL: str = "http://localhost:9104"

    class Config:
        env_file=".env"

@lru_cache()
def get_settings():
    return Settings()

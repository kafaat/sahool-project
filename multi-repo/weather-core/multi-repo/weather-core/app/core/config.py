from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/sahool"

    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
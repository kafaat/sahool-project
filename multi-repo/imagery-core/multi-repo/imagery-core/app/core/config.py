
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/sahool"
    STORAGE_PATH: str = "/code/storage"
    CDSE_USER: str = "user"
    CDSE_PASS: str = "pass"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

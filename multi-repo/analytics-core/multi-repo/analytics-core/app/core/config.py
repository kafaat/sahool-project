
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/sahool"
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

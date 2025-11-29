from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    GATEWAY_URL: str = "http://gateway-edge:9000"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    REDIS_URL: str = "redis://sahool-redis:6379/0"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()

from pydantic import BaseSettings

class Settings(BaseSettings):
    ENV: str = "local"
    LOG_LEVEL: str = "info"

    GATEWAY_URL: str = "http://gateway-edge:9000"
    MINIO_ENDPOINT: str = "http://sahool-minio:9000"
    MINIO_BUCKET_IMAGERY: str = "sahool-imagery"
    MINIO_BUCKET_NDVI: str = "sahool-ndvi"
    REDIS_URL: str = "redis://sahool-redis:6379/0"

    class Config:
        case_sensitive = True

settings = Settings()

from fastapi import FastAPI
from pydantic import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = "redis://sahool-redis:6379/0"

    class Config:
        case_sensitive = True

settings = Settings()
app = FastAPI(title="Sahool Events Bus")

@app.get("/health")
def health():
    return {"status": "ok", "service": "events-bus"}

from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title="Sahool Weather Ingestor")

@app.get("/health")
def health():
    return {"status": "ok", "service": "weather-ingestor"}

app.include_router(router)

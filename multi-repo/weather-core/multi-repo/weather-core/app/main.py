import os
from fastapi import FastAPI
from app.api.routes.weather import router as weather_router

app = FastAPI(title="weather-core", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "weather-core"}

app.include_router(weather_router)
@app.get("/info")
def info():
    return {
        "service": "weather-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

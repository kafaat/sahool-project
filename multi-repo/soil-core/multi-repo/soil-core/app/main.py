import os
from fastapi import FastAPI
from app.api.routes.soil import router as soil_router

app = FastAPI(title="soil-core", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "soil-core"}

app.include_router(soil_router)
@app.get("/info")
def info():
    return {
        "service": "soil-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

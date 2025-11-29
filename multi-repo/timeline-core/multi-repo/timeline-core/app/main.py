import os
from fastapi import FastAPI
from app.core.config import settings
from app.api.routes.timeline import router as timeline_router

app = FastAPI(title="Sahool Timeline Core")

@app.get("/health")
def health():
    return {"status": "ok", "service": "timeline-core"}

app.include_router(timeline_router)
@app.get("/info")
def info():
    return {
        "service": "timeline-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

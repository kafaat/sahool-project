
import os
from fastapi import FastAPI
from app.api.routes.analytics import router as analytics_router

app = FastAPI(title="analytics-core", version="1.0.0")

@app.get("/health")
def health():
    return {"service": "analytics-core", "status": "ok"}

app.include_router(analytics_router)
@app.get("/info")
def info():
    return {
        "service": "analytics-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

import os
from fastapi import FastAPI
from app.api.routes.alerts import router as alerts_router

app = FastAPI(title="alerts-core", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "alerts-core"}

app.include_router(alerts_router)
@app.get("/info")
def info():
    return {
        "service": "alerts-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

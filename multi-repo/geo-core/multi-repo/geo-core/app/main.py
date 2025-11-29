import os
from fastapi import FastAPI

from app.api.routes.fields import router as fields_router

app = FastAPI(title="geo-core", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "geo-core"}


app.include_router(fields_router)
@app.get("/info")
def info():
    return {
        "service": "geo-core",
        "version": getattr(app, "version", "1.0.0"),
        "environment": os.getenv("SAHOOL_ENV", "local"),
    }

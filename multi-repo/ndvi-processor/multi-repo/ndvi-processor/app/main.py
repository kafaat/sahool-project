from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title="Sahool NDVI Processor")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ndvi-processor"}

app.include_router(router)

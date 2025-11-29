from fastapi import FastAPI
from app.api.routes.images import router as imagery_router

app = FastAPI(title="imagery-core", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "imagery-core"}

app.include_router(imagery_router)

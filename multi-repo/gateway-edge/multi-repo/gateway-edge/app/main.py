
from fastapi import FastAPI
from app.routes.router import router as api_router

app=FastAPI(title="gateway-edge", version="1.0.0")

@app.get("/health")
def health():
    return {"service":"gateway-edge","status":"ok"}

app.include_router(api_router)

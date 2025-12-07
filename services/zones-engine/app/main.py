import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Zones Engine",
    version="5.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - use specific origins in production
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)  # Only allow credentials with specific origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,  # False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "zones-engine",
        "version": "5.5.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/field/{field_id}")
async def get_management_zones(field_id: str):
    """Get management zones for a field"""
    return {
        "success": True,
        "data": [],
        "message": "Management zones retrieved successfully"
    }


@app.post("/calculate/{field_id}")
async def calculate_zones(field_id: str):
    """Calculate management zones for a field based on NDVI data"""
    return {
        "success": True,
        "data": {
            "fieldId": field_id,
            "zonesCount": 0,
            "zones": []
        },
        "message": "Zones calculated successfully"
    }


@app.get("/")
async def root():
    return {
        "service": "zones-engine",
        "version": "5.5.0",
        "description": "Management Zones Engine",
        "endpoints": [
            "GET /health",
            "GET /field/{field_id}",
            "POST /calculate/{field_id}",
            "GET /docs"
        ]
    }

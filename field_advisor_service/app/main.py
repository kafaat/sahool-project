"""
Field Advisor Service - Main Application
Smart Agricultural Advisory System
"""
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.logging import logger
from .models import Base, engine
from .api.routes import advisor_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.service_name}")


# Create FastAPI app
app = FastAPI(
    title="Field Advisor Service",
    description="""
    ## Smart Agricultural Advisory System

    Field Advisor provides intelligent recommendations for agricultural field management
    based on NDVI analysis, weather data, crop information, and soil conditions.

    ### Features:
    - **Field Analysis**: Comprehensive field health assessment
    - **Recommendations**: Actionable irrigation, fertilization, and pest control advice
    - **Alerts**: Real-time alerts for critical field conditions
    - **Playbook**: Scheduled action plans for field management
    - **Action Tracking**: Log and monitor field interventions

    ### Architecture:
    ```
    ┌─────────────────────┐
    │   Context Aggregator │ ──► NDVI, Weather, Crop, Soil
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Rules Engine      │ ──► Generate Recommendations & Alerts
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Recommendation Store │ ──► Sessions, Recommendations, Alerts, Actions
    └─────────────────────┘
    ```
    """,
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"[{request_id}]"
    )

    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"

    # Log response
    logger.info(
        f"Response: {response.status_code} "
        f"[{request_id}] {duration:.2f}ms"
    )

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception [{request_id}]: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(health_router)
app.include_router(advisor_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Service information"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Smart Agricultural Advisory System",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "POST /advisor/analyze-field",
            "recommendations": "GET /advisor/recommendations/{field_id}",
            "alerts": "GET /advisor/alerts/{field_id}",
            "playbook": "POST /advisor/playbook",
            "actions": "GET /advisor/actions/{field_id}",
            "stats": "GET /advisor/stats/{field_id}",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
    )

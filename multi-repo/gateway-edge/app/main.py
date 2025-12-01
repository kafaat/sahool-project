"""
Sahool API Gateway - Edge Service
Central API Gateway for routing requests to microservices
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging
import time
import os
from typing import Callable

from .routes.proxy_geo import router as proxy_geo
from .routes.proxy_imagery import router as proxy_imagery
from .routes.proxy_weather import router as proxy_weather
from .routes.proxy_soil import router as proxy_soil
from .routes.proxy_alerts import router as proxy_alerts
from .routes.nano_routes import router as nano_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Sahool API Gateway...")
    logger.info("📡 Initializing microservice connections...")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Sahool API Gateway...")


# Create FastAPI application
app = FastAPI(
    title="Sahool API Gateway",
    description="Central API Gateway for Sahool Agricultural Platform",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add state for rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS Configuration - Secure
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:9000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
    max_age=3600,
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host middleware (security)
trusted_hosts = os.getenv("TRUSTED_HOSTS", "*").split(",")
if "*" not in trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Log all incoming requests"""
    start_time = time.time()

    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")

    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        return response

    except Exception as e:
        logger.error(f"❌ Error processing request: {e}", exc_info=True)
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(
        f"❌ Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"⚠️  HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )


# Health check endpoints
@app.get("/", tags=["System"])
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Sahool API Gateway",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["System"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Health check endpoint

    Returns the health status of the API Gateway
    """
    return {
        "status": "healthy",
        "service": "gateway-edge",
        "version": "3.0.0",
        "timestamp": time.time()
    }


@app.get("/health/detailed", tags=["System"])
@limiter.limit("10/minute")
async def detailed_health_check(request: Request):
    """
    Detailed health check

    Returns detailed health information including microservice status
    """
    # TODO: Add microservice health checks
    return {
        "status": "healthy",
        "service": "gateway-edge",
        "version": "3.0.0",
        "timestamp": time.time(),
        "services": {
            "geo-core": "unknown",
            "imagery-core": "unknown",
            "weather-core": "unknown",
            "soil-core": "unknown",
            "alerts-core": "unknown"
        }
    }


@app.get("/metrics", tags=["System"])
@limiter.limit("10/minute")
async def metrics(request: Request):
    """
    Basic metrics endpoint

    Returns basic metrics for monitoring
    """
    # TODO: Implement proper metrics collection
    return {
        "requests_total": "N/A",
        "requests_per_second": "N/A",
        "average_response_time": "N/A",
        "error_rate": "N/A"
    }


# Include microservice proxy routers
app.include_router(
    proxy_geo,
    prefix="/api/geo",
    tags=["Geo Service"]
)

app.include_router(
    proxy_imagery,
    prefix="/api/imagery",
    tags=["Imagery Service"]
)

app.include_router(
    proxy_weather,
    prefix="/api/weather",
    tags=["Weather Service"]
)

app.include_router(
    proxy_soil,
    prefix="/api/soil",
    tags=["Soil Service"]
)

app.include_router(
    proxy_alerts,
    prefix="/api/alerts",
    tags=["Alerts Service"]
)

app.include_router(
    nano_router,
    tags=["Additional Routes"]
)


# Startup message
@app.on_event("startup")
async def startup_event():
    """Log startup message"""
    logger.info("=" * 60)
    logger.info("  Sahool API Gateway v3.0.0")
    logger.info("  Environment: " + os.getenv("SAHOOL_ENV", "development"))
    logger.info("  Allowed Origins: " + ", ".join(allowed_origins))
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info",
        access_log=True
    )

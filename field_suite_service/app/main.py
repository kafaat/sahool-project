"""
سهول اليمن - Field Suite Backend Main Application
المنصة الزراعية الذكية لليمن - الخدمة الرئيسية

Enhanced with:
- Circuit Breaker & Retry Logic
- Redis Caching
- Rate Limiting & Security
- WebSocket Real-time Updates
- Advanced Monitoring
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import structlog
import httpx

# Import core modules
from app.core.config import get_settings
from app.core.resilience import (
    CircuitBreakerConfig,
    circuit_registry,
    with_circuit_breaker,
    with_retry,
    RetryConfig,
    Bulkhead,
)
from app.core.cache import cache_manager, cached
from app.core.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    rate_limiter,
    InputValidator,
)
from app.core.websocket import (
    connection_manager,
    websocket_endpoint,
    event_emitter,
    ws_background_tasks,
    YemenChannels,
)
from app.core.monitoring import (
    MetricsMiddleware,
    RequestLoggingMiddleware,
    health_checker,
    system_metrics,
    configure_logging,
    set_app_info,
)

# Configure structured logging
configure_logging(service_name="sahool-yemen", log_level="INFO", json_format=True)
logger = structlog.get_logger(__name__)

# Settings
settings = get_settings()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

# Service URLs from environment
IMAGERY_CORE_URL = os.getenv("IMAGERY_CORE_BASE_URL", "http://imagery-core:8000")
ANALYTICS_CORE_URL = os.getenv("ANALYTICS_CORE_BASE_URL", "http://analytics-core:8000")
GEO_CORE_URL = os.getenv("GEO_CORE_BASE_URL", "http://geo-core:8000")
WEATHER_CORE_URL = os.getenv("WEATHER_CORE_BASE_URL", "http://weather-core:8000")
ADVISOR_CORE_URL = os.getenv("ADVISOR_CORE_BASE_URL", "http://advisor-core:8000")
QUERY_CORE_URL = os.getenv("QUERY_CORE_BASE_URL", "http://query-core:8000")

# HTTP client
http_client: Optional[httpx.AsyncClient] = None

# Bulkheads for resource isolation
weather_bulkhead = Bulkhead("weather", max_concurrent=20)
imagery_bulkhead = Bulkhead("imagery", max_concurrent=15)
analytics_bulkhead = Bulkhead("analytics", max_concurrent=25)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global http_client

    # Startup
    logger.info("starting_service", version="6.0.0", service="sahool-yemen")

    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
    )

    # Initialize cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    await cache_manager.initialize(redis_url)

    # Start background tasks
    await ws_background_tasks.start()
    await system_metrics.start()

    # Register health checks
    health_checker.register("http_client", lambda: {"healthy": http_client is not None})
    health_checker.register("cache", lambda: cache_manager.get_stats())
    health_checker.register("websocket", lambda: connection_manager.get_stats())

    # Set application info for metrics
    set_app_info(version="6.0.0", service_name="sahool-yemen")

    logger.info("service_started", components=["cache", "websocket", "metrics"])

    yield

    # Shutdown
    logger.info("shutting_down_service")

    await ws_background_tasks.stop()
    await system_metrics.stop()
    await cache_manager.shutdown()

    if http_client:
        await http_client.aclose()

    logger.info("service_stopped")


app = FastAPI(
    title="سهول اليمن - Field Suite API",
    description="""
    المنصة الزراعية الذكية لليمن

    ## الميزات الرئيسية
    - 🌱 تحليل صحة المحاصيل باستخدام NDVI
    - 🌤️ بيانات الطقس والتنبؤات
    - 💧 توصيات الري الذكية
    - 📊 تحليلات وإحصاءات شاملة
    - 🤖 مستشار زراعي ذكي
    - 🔄 تحديثات مباشرة عبر WebSocket
    - 🛡️ حماية أمنية متقدمة

    ## المحافظات المدعومة
    جميع المحافظات اليمنية العشرون
    """,
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware (order matters - last added is first executed)
app.add_middleware(MetricsMiddleware, exclude_paths=["/metrics", "/health"])
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
app.add_middleware(SecurityHeadersMiddleware)
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


# =============================================================================
# Health Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "sahool-yemen",
        "version": "6.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check with all dependencies"""
    result = await health_checker.run_all_checks()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check"""
    return await health_checker.liveness_check()


# =============================================================================
# Metrics & Monitoring Endpoints
# =============================================================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/status", tags=["Monitoring"])
async def system_status():
    """System status with detailed component information"""
    return {
        "service": "sahool-yemen",
        "version": "6.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "cache": cache_manager.get_stats(),
            "websocket": connection_manager.get_stats(),
            "circuit_breakers": circuit_registry.get_all_stats(),
            "rate_limiter": {"requests_per_second": settings.rate_limit_requests},
        },
        "system": system_metrics.get_system_info(),
    }


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/{client_id}")
async def ws_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates

    Channels:
    - field:{field_id} - Field updates
    - weather:{region_id} - Weather updates
    - alerts - System alerts
    - ndvi - NDVI updates
    """
    await websocket_endpoint(websocket, client_id)


# =============================================================================
# Proxy Functions with Circuit Breaker
# =============================================================================

@with_circuit_breaker("weather-core", CircuitBreakerConfig(failure_threshold=5, timeout=30))
@with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
async def call_weather_service(path: str, method: str = "GET", body: bytes = None, headers: dict = None):
    """Call weather service with circuit breaker and retry"""
    async with weather_bulkhead:
        url = f"{WEATHER_CORE_URL}{path}"
        if method == "GET":
            response = await http_client.get(url, headers=headers)
        else:
            response = await http_client.post(url, content=body, headers=headers)
        response.raise_for_status()
        return response.json()


@with_circuit_breaker("imagery-core", CircuitBreakerConfig(failure_threshold=5, timeout=30))
@with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
async def call_imagery_service(path: str, method: str = "GET", body: bytes = None, headers: dict = None):
    """Call imagery service with circuit breaker and retry"""
    async with imagery_bulkhead:
        url = f"{IMAGERY_CORE_URL}{path}"
        if method == "GET":
            response = await http_client.get(url, headers=headers)
        else:
            response = await http_client.post(url, content=body, headers=headers)
        response.raise_for_status()
        return response.json()


async def _proxy_request(request: Request, base_url: str, path: str):
    """Helper function to proxy requests to nano services"""
    url = f"{base_url}{path}"

    # Forward query parameters
    if request.query_params:
        url += f"?{request.query_params}"

    try:
        if request.method == "GET":
            response = await http_client.get(url, headers=dict(request.headers))
        else:
            body = await request.body()
            response = await http_client.post(
                url,
                content=body,
                headers=dict(request.headers)
            )

        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error("proxy_error", error=str(e), url=url)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Proxy Endpoints to Nano Services
# =============================================================================

@app.api_route("/v1/weather/{path:path}", methods=["GET", "POST"], tags=["Weather"])
async def proxy_weather(request: Request, path: str):
    """Proxy requests to Weather Core service"""
    return await _proxy_request(request, WEATHER_CORE_URL, f"/api/v1/weather/{path}")


@app.api_route("/v1/ndvi/{path:path}", methods=["GET", "POST"], tags=["NDVI"])
async def proxy_ndvi(request: Request, path: str):
    """Proxy requests to Imagery Core service"""
    return await _proxy_request(request, IMAGERY_CORE_URL, f"/api/v1/ndvi/{path}")


@app.api_route("/v1/geo/{path:path}", methods=["GET", "POST"], tags=["Geo"])
async def proxy_geo(request: Request, path: str):
    """Proxy requests to Geo Core service"""
    return await _proxy_request(request, GEO_CORE_URL, f"/api/v1/geo/{path}")


@app.api_route("/v1/analytics/{path:path}", methods=["GET", "POST"], tags=["Analytics"])
async def proxy_analytics(request: Request, path: str):
    """Proxy requests to Analytics Core service"""
    return await _proxy_request(request, ANALYTICS_CORE_URL, f"/api/v1/{path}")


@app.api_route("/v1/fields/{path:path}", methods=["GET", "POST"], tags=["Fields"])
async def proxy_fields(request: Request, path: str):
    """Proxy requests to Query Core service"""
    return await _proxy_request(request, QUERY_CORE_URL, f"/api/v1/fields/{path}")


@app.api_route("/v1/advisor/{path:path}", methods=["GET", "POST"], tags=["Advisor"])
async def proxy_advisor(request: Request, path: str):
    """Proxy requests to Advisor Core service"""
    return await _proxy_request(request, ADVISOR_CORE_URL, f"/api/v1/advisor/{path}")


# =============================================================================
# Direct Endpoints (with Caching)
# =============================================================================

@app.get("/v1/regions", tags=["Regions"])
@cached(ttl=86400, key_prefix="regions")  # Cache for 24 hours
async def list_regions():
    """قائمة المحافظات اليمنية"""
    regions = [
        {"id": 1, "name_ar": "صنعاء", "name_en": "Sanaa", "lat": 15.3547, "lon": 44.2067},
        {"id": 2, "name_ar": "عدن", "name_en": "Aden", "lat": 12.8254, "lon": 45.0339},
        {"id": 3, "name_ar": "تعز", "name_en": "Taiz", "lat": 13.5782, "lon": 44.0107},
        {"id": 4, "name_ar": "حضرموت", "name_en": "Hadramaut", "lat": 15.4768, "lon": 48.8318},
        {"id": 5, "name_ar": "الحديدة", "name_en": "Hudaydah", "lat": 14.7974, "lon": 42.9531},
        {"id": 6, "name_ar": "إب", "name_en": "Ibb", "lat": 14.1446, "lon": 43.9440},
        {"id": 7, "name_ar": "ذمار", "name_en": "Dhamar", "lat": 15.5570, "lon": 44.4137},
        {"id": 8, "name_ar": "شبوة", "name_en": "Shabwah", "lat": 14.3801, "lon": 45.7186},
        {"id": 9, "name_ar": "لحج", "name_en": "Lahij", "lat": 13.0565, "lon": 44.8812},
        {"id": 10, "name_ar": "أبين", "name_en": "Abyan", "lat": 13.6950, "lon": 45.8824},
        {"id": 11, "name_ar": "مأرب", "name_en": "Marib", "lat": 15.4620, "lon": 45.3406},
        {"id": 12, "name_ar": "الجوف", "name_en": "Al Jawf", "lat": 16.7206, "lon": 44.8154},
        {"id": 13, "name_ar": "عمران", "name_en": "Amran", "lat": 16.2564, "lon": 43.9430},
        {"id": 14, "name_ar": "حجة", "name_en": "Hajjah", "lat": 16.1235, "lon": 43.3250},
        {"id": 15, "name_ar": "المحويت", "name_en": "Mahwit", "lat": 15.2589, "lon": 43.5400},
        {"id": 16, "name_ar": "ريمة", "name_en": "Raymah", "lat": 14.4000, "lon": 44.5000},
        {"id": 17, "name_ar": "المهرة", "name_en": "Al Mahrah", "lat": 16.5000, "lon": 51.8000},
        {"id": 18, "name_ar": "سقطرى", "name_en": "Soqatra", "lat": 12.5000, "lon": 53.8000},
        {"id": 19, "name_ar": "البيضاء", "name_en": "Al Bayda", "lat": 14.2000, "lon": 45.3000},
        {"id": 20, "name_ar": "صعدة", "name_en": "Saadah", "lat": 16.9000, "lon": 43.7000},
    ]
    return {"regions": regions, "count": len(regions)}


@app.get("/v1/crops", tags=["Crops"])
@cached(ttl=86400, key_prefix="crops")  # Cache for 24 hours
async def list_crops():
    """قائمة المحاصيل الزراعية"""
    crops = [
        {"id": 1, "name_ar": "قمح", "name_en": "Wheat", "season": "شتاء", "ndvi_range": [0.3, 0.7]},
        {"id": 2, "name_ar": "ذرة", "name_en": "Corn", "season": "صيف", "ndvi_range": [0.4, 0.8]},
        {"id": 3, "name_ar": "شعير", "name_en": "Barley", "season": "شتاء", "ndvi_range": [0.3, 0.65]},
        {"id": 4, "name_ar": "بن", "name_en": "Coffee", "season": "على مدار السنة", "ndvi_range": [0.5, 0.85]},
        {"id": 5, "name_ar": "طماطم", "name_en": "Tomato", "season": "ربيع/خريف", "ndvi_range": [0.35, 0.75]},
        {"id": 6, "name_ar": "بصل", "name_en": "Onion", "season": "خريف", "ndvi_range": [0.25, 0.6]},
        {"id": 7, "name_ar": "بطاطس", "name_en": "Potato", "season": "ربيع", "ndvi_range": [0.3, 0.7]},
        {"id": 8, "name_ar": "خضروات", "name_en": "Vegetables", "season": "متعدد", "ndvi_range": [0.3, 0.75]},
        {"id": 9, "name_ar": "فواكه", "name_en": "Fruits", "season": "متعدد", "ndvi_range": [0.4, 0.8]},
        {"id": 10, "name_ar": "أعلاف", "name_en": "Fodder", "season": "على مدار السنة", "ndvi_range": [0.35, 0.7]},
    ]
    return {"crops": crops, "count": len(crops)}


@app.get("/v1/dashboard", tags=["Dashboard"])
@cached(ttl=300, key_prefix="dashboard")  # Cache for 5 minutes
async def get_dashboard():
    """بيانات لوحة التحكم الرئيسية"""
    import random

    return {
        "summary": {
            "total_farmers": random.randint(15000, 25000),
            "total_fields": random.randint(40000, 60000),
            "total_area_ha": random.randint(150000, 300000),
            "active_regions": 20,
        },
        "ndvi_status": {
            "excellent": random.randint(30, 40),
            "good": random.randint(30, 40),
            "moderate": random.randint(15, 25),
            "poor": random.randint(5, 15),
        },
        "alerts": {
            "high": random.randint(5, 15),
            "medium": random.randint(10, 30),
            "low": random.randint(20, 50),
        },
        "weather": {
            "avg_temp_celsius": round(random.uniform(22, 32), 1),
            "rain_probability": random.randint(0, 40),
        },
        "last_updated": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Real-time Broadcast Endpoints (for testing)
# =============================================================================

@app.post("/v1/broadcast/alert", tags=["Real-time"])
async def broadcast_alert(alert: dict):
    """Broadcast an alert to all connected clients"""
    await event_emitter.emit_system_alert(alert)
    return {"status": "sent", "connections": connection_manager.get_stats()["active_connections"]}


@app.post("/v1/broadcast/weather/{region_id}", tags=["Real-time"])
async def broadcast_weather(region_id: int, weather: dict):
    """Broadcast weather update to region subscribers"""
    # Validate region ID
    valid, msg = InputValidator.validate_region_id(region_id)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    await event_emitter.emit_weather_update(region_id, weather)
    subscribers = connection_manager.get_channel_subscribers(YemenChannels.weather(region_id))
    return {"status": "sent", "subscribers": len(subscribers)}


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_ar": "خطأ داخلي في الخادم",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

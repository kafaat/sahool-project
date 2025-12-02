"""
سهول اليمن - Field Suite Backend Main Application
المنصة الزراعية الذكية لليمن - الخدمة الرئيسية
"""
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import structlog
import httpx

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global http_client

    # Startup
    logger.info("Starting Field Suite Backend Service", version="6.0.0")
    http_client = httpx.AsyncClient(timeout=30.0)

    yield

    # Shutdown
    logger.info("Shutting down Field Suite Backend Service")
    if http_client:
        await http_client.aclose()

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

    ## المحافظات المدعومة
    جميع المحافظات اليمنية العشرون
    """,
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    response = await call_next(request)

    duration = (datetime.utcnow() - start_time).total_seconds()

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration,
    )

    return response

# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "field-suite-backend",
        "version": "6.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check with service dependencies"""
    services_status = {}

    # Check nano services
    service_urls = {
        "weather-core": f"{WEATHER_CORE_URL}/health",
        "imagery-core": f"{IMAGERY_CORE_URL}/health",
        "geo-core": f"{GEO_CORE_URL}/health",
        "analytics-core": f"{ANALYTICS_CORE_URL}/health",
        "query-core": f"{QUERY_CORE_URL}/health",
        "advisor-core": f"{ADVISOR_CORE_URL}/health",
    }

    for service_name, url in service_urls.items():
        try:
            response = await http_client.get(url, timeout=5.0)
            services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            services_status[service_name] = f"unavailable: {str(e)}"

    all_healthy = all(status == "healthy" for status in services_status.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Proxy endpoints to nano services
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

# Direct endpoints
@app.get("/v1/regions", tags=["Regions"])
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
async def list_crops():
    """قائمة المحاصيل الزراعية"""
    crops = [
        {"name_ar": "قمح", "name_en": "Wheat", "season": "شتاء"},
        {"name_ar": "ذرة", "name_en": "Corn", "season": "صيف"},
        {"name_ar": "شعير", "name_en": "Barley", "season": "شتاء"},
        {"name_ar": "بن", "name_en": "Coffee", "season": "على مدار السنة"},
        {"name_ar": "طماطم", "name_en": "Tomato", "season": "ربيع/خريف"},
        {"name_ar": "بصل", "name_en": "Onion", "season": "خريف"},
        {"name_ar": "بطاطس", "name_en": "Potato", "season": "ربيع"},
        {"name_ar": "خضروات", "name_en": "Vegetables", "season": "متعدد"},
        {"name_ar": "فواكه", "name_en": "Fruits", "season": "متعدد"},
        {"name_ar": "أعلاف", "name_en": "Fodder", "season": "على مدار السنة"},
    ]
    return {"crops": crops, "count": len(crops)}

@app.get("/v1/dashboard", tags=["Dashboard"])
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

# Error handlers
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

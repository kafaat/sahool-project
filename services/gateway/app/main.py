"""
API Gateway Service - بوابة API
Sahool Yemen v9.0.0

Central API Gateway for routing requests to microservices.
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

import sys
sys.path.insert(0, "/app/libs-shared")

from sahool_shared.auth import get_current_user, AuthenticatedUser, verify_token
from sahool_shared.cache import get_cache, RedisCache
from sahool_shared.utils import setup_logging, get_logger
from sahool_shared.schemas.common import HealthResponse, ErrorResponse

# Configuration
SERVICE_ROUTES = {
    "/api/v1/weather": os.getenv("WEATHER_SERVICE_URL", "http://weather-service:8000"),
    "/api/v1/ndvi": os.getenv("NDVI_SERVICE_URL", "http://ndvi-service:8000"),
    "/api/v1/fields": os.getenv("FIELD_SERVICE_URL", "http://field-service:8000"),
    "/api/v1/alerts": os.getenv("ALERT_SERVICE_URL", "http://alert-service:8000"),
    "/api/v1/analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
    "/api/v1/auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/v1/users": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "/api/v1/tenants": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
}

# Rate limiting config
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "200"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Metrics
REQUEST_COUNT = Counter("gateway_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("gateway_request_latency_seconds", "Request latency", ["method", "path"])
UPSTREAM_LATENCY = Histogram("gateway_upstream_latency_seconds", "Upstream service latency", ["service"])

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization", "")

        # Use user ID from token if available, otherwise use IP
        rate_key = client_ip
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = verify_token(token)
                rate_key = f"user:{payload.sub}"
            except Exception as e:
                # Token invalid/expired - fall back to IP-based rate limiting
                logger.debug("token_verification_for_rate_limit_failed", error=str(e), client=client_ip)

        # Check rate limit
        try:
            cache = await get_cache()
            allowed, count = await cache.rate_limit_check(
                f"gateway:{rate_key}",
                limit=RATE_LIMIT_REQUESTS,
                window=RATE_LIMIT_WINDOW,
            )

            if not allowed:
                logger.warning("rate_limit_exceeded", client=rate_key, count=count)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "تم تجاوز حد الطلبات. حاول مرة أخرى لاحقاً.",
                        "retry_after": RATE_LIMIT_WINDOW,
                    },
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
                )
        except Exception as e:
            logger.error("rate_limit_check_failed", error=str(e))
            # Fail open with warning header - allows request but indicates rate limit check failed
            # In production, consider failing closed (returning 503) for security
            response = await call_next(request)
            response.headers["X-Rate-Limit-Status"] = "unavailable"
            return response

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(time.time()))

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            REQUEST_COUNT.labels(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                path=request.url.path,
            ).observe(duration)

            logger.info(
                "request_completed",
                request_id=request_id,
                status=response.status_code,
                duration=f"{duration:.3f}s",
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            return response

        except Exception as e:
            logger.error(
                "request_failed",
                request_id=request_id,
                error=str(e),
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="api-gateway")
    logger.info("api_gateway_starting", version="9.0.0", routes=list(SERVICE_ROUTES.keys()))
    yield
    logger.info("api_gateway_stopping")


app = FastAPI(
    title="Sahool Yemen API Gateway",
    description="بوابة API لمنصة سهول اليمن",
    version="9.0.0",
    lifespan=lifespan,
)

# CORS Configuration - use specific origins in production
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)  # Only allow credentials with specific origins

# Startup warning for CORS configuration
if not CORS_ORIGINS:
    logger.warning(
        "cors_not_configured",
        message="CORS_ORIGINS not set - using wildcard '*' without credentials. "
                "Authentication cookies will NOT work. Set CORS_ORIGINS for production."
    )

# Add middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,  # False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for proxying
http_client = httpx.AsyncClient(timeout=30.0)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Gateway health check."""
    return HealthResponse(
        status="healthy",
        version="9.0.0",
        service="api-gateway"
    )


@app.get("/health/services")
async def services_health():
    """Check health of all backend services."""
    results = {}

    for path, url in SERVICE_ROUTES.items():
        service_name = path.split("/")[-1]
        try:
            response = await http_client.get(f"{url}/health", timeout=5.0)
            results[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
            }
        except Exception as e:
            results[service_name] = {
                "status": "unhealthy",
                "error": str(e),
            }

    overall = "healthy" if all(s["status"] == "healthy" for s in results.values()) else "degraded"

    return {
        "status": overall,
        "services": results,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


def get_upstream_url(path: str) -> Optional[str]:
    """Get upstream service URL for a path."""
    for route_prefix, service_url in SERVICE_ROUTES.items():
        if path.startswith(route_prefix):
            return service_url
    return None


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_request(request: Request, path: str):
    """
    Proxy requests to backend services.
    توجيه الطلبات إلى الخدمات الخلفية
    """
    full_path = f"/api/{path}"
    upstream_url = get_upstream_url(full_path)

    if not upstream_url:
        raise HTTPException(
            status_code=404,
            detail=f"لا يوجد خدمة للمسار: {full_path}"
        )

    # Build upstream URL
    target_url = f"{upstream_url}{full_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Forwarded-Proto"] = request.url.scheme

    # Get request body
    body = await request.body()

    try:
        start_time = time.time()

        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

        upstream_time = time.time() - start_time
        service_name = full_path.split("/")[3] if len(full_path.split("/")) > 3 else "unknown"
        UPSTREAM_LATENCY.labels(service=service_name).observe(upstream_time)

        # Return response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type"),
        )

    except httpx.TimeoutException:
        logger.error("upstream_timeout", url=target_url)
        raise HTTPException(
            status_code=504,
            detail="انتهت مهلة الخدمة. حاول مرة أخرى."
        )
    except httpx.ConnectError:
        logger.error("upstream_connection_error", url=target_url)
        raise HTTPException(
            status_code=503,
            detail="الخدمة غير متاحة حالياً."
        )
    except Exception as e:
        logger.error("proxy_error", url=target_url, error=str(e))
        raise HTTPException(
            status_code=502,
            detail="خطأ في الاتصال بالخدمة."
        )


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await http_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

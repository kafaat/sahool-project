"""
Enhanced Geo-Core with Error Handling, Validation, and Resilience
مثال على دمج جميع أنظمة تقليل الأخطاء
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import error handling
import sys
sys.path.append('/home/user/sahool-project')

from shared.error_handling import (
    SahoolException,
    sahool_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

from shared.health_checks import (
    HealthCheckManager,
    DatabaseHealthChecker,
    ServiceHealthChecker,
    DiskHealthChecker,
    MemoryHealthChecker
)

from shared.resilience import (
    db_circuit_breaker,
    ml_circuit_breaker,
    external_api_circuit_breaker
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sahool/geo-core.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ===================================================================
# APP LIFECYCLE
# ===================================================================

health_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""

    # Startup
    logger.info("🚀 Starting Geo-Core service with enhanced error handling...")

    global health_manager
    health_manager = HealthCheckManager(app_version="3.2.1")

    # Add health checkers
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sahool")
    health_manager.add_checker(DatabaseHealthChecker(db_url))

    # Check other services
    health_manager.add_checker(ServiceHealthChecker(
        name="ml-engine",
        url="http://ml-engine:8010/health",
        timeout=5.0
    ))

    health_manager.add_checker(ServiceHealthChecker(
        name="agent-ai",
        url="http://agent-ai:8002/health",
        timeout=5.0
    ))

    # System resources
    health_manager.add_checker(DiskHealthChecker())
    health_manager.add_checker(MemoryHealthChecker())

    logger.info("✅ Health checks initialized")

    # Run initial health check
    try:
        initial_health = await health_manager.check_all()
        logger.info(f"📊 Initial health status: {initial_health.status}")

        for component in initial_health.components:
            logger.info(f"  - {component.name}: {component.status} ({component.response_time_ms}ms)")

    except Exception as e:
        logger.error(f"❌ Initial health check failed: {e}")

    yield

    # Shutdown
    logger.info("👋 Shutting down Geo-Core service...")

# ===================================================================
# CREATE APP
# ===================================================================

app = FastAPI(
    title="Sahool Geo-Core (Enhanced)",
    description="Geographic Information Service with Advanced Error Handling",
    version="3.2.1",
    lifespan=lifespan
)

# ===================================================================
# MIDDLEWARE
# ===================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    import time

    start_time = time.time()

    # Log request
    logger.info(f"➡️  {request.method} {request.url.path} - Request ID: {request.state.request_id}")

    try:
        response = await call_next(request)

        # Calculate duration
        duration = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"⬅️  {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.2f}ms - "
            f"Request ID: {request.state.request_id}"
        )

        # Add duration header
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        logger.error(
            f"❌ {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Duration: {duration:.2f}ms - "
            f"Request ID: {request.state.request_id}",
            exc_info=True
        )

        raise

# ===================================================================
# EXCEPTION HANDLERS
# ===================================================================

# Register exception handlers
app.add_exception_handler(SahoolException, sahool_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ===================================================================
# HEALTH ENDPOINTS
# ===================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return await health_manager.check_all()

@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    health = await health_manager.check_all()

    if health.status == "unhealthy":
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "Service unhealthy"}
        )

    return {"status": "ready"}

# ===================================================================
# CIRCUIT BREAKER METRICS
# ===================================================================

@app.get("/metrics/circuit-breakers")
async def circuit_breaker_metrics():
    """Circuit breaker status and metrics"""
    return {
        "database": db_circuit_breaker.get_metrics(),
        "ml_engine": ml_circuit_breaker.get_metrics(),
        "external_api": external_api_circuit_breaker.get_metrics()
    }

# ===================================================================
# EXAMPLE ROUTES WITH ERROR HANDLING
# ===================================================================

from shared.validation import ValidatedFieldCreate, GeometryValidator
from shared.error_handling import (
    ValidationException,
    NotFoundException,
    TenantAccessException,
    DatabaseException
)
from shared.resilience import resilient, RetryConfig, timeout

@app.post("/api/v2/fields")
@limiter.limit("20/minute")
async def create_field_enhanced(
    request: Request,
    field_data: ValidatedFieldCreate  # Automatic validation
):
    """
    Create field with comprehensive error handling

    Features:
    - Automatic input validation (Pydantic)
    - Geometry validation
    - Database retry with exponential backoff
    - Circuit breaker for database
    - Timeout protection
    - Structured error responses
    """

    logger.info(f"Creating field: {field_data.name}")

    # Additional geometry validation (already done by Pydantic, but example)
    try:
        GeometryValidator.validate_geojson(field_data.geometry)
    except Exception as e:
        logger.warning(f"Geometry validation failed: {e}")
        raise

    # Save to database with resilience
    @resilient(
        retry_config=RetryConfig(max_attempts=3),
        circuit_breaker=db_circuit_breaker,
        timeout_seconds=10.0
    )
    async def save_field():
        # Simulate database save
        # In real code: await db.execute(...)
        import asyncio
        await asyncio.sleep(0.1)

        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": field_data.name,
            "crop": field_data.crop,
            "status": "created"
        }

    try:
        result = await save_field()
        logger.info(f"✅ Field created successfully: {result['id']}")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to create field: {e}")
        raise DatabaseException("create_field", e)

@app.get("/api/v2/fields/{field_id}")
@limiter.limit("60/minute")
async def get_field_enhanced(
    request: Request,
    field_id: str
):
    """
    Get field with proper error handling

    Features:
    - Not found handling
    - Tenant isolation check
    - Database circuit breaker
    """

    logger.info(f"Fetching field: {field_id}")

    # Simulate database query
    @timeout(5.0)
    async def fetch_field():
        import asyncio
        await asyncio.sleep(0.05)

        # Simulate not found
        if field_id == "not-found":
            return None

        return {
            "id": field_id,
            "name": "Test Field",
            "crop": "tomato",
            "tenant_id": "tenant-123"
        }

    try:
        field = await fetch_field()

        if not field:
            raise NotFoundException("Field", field_id)

        # Check tenant access (example)
        # current_user = Depends(get_current_user)
        # if field.tenant_id != current_user.tenant_id:
        #     raise TenantAccessException(current_user.tenant_id, field_id)

        logger.info(f"✅ Field retrieved: {field_id}")
        return field

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch field: {e}")
        raise DatabaseException("get_field", e)

# ===================================================================
# ROOT ENDPOINT
# ===================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "service": "Sahool Geo-Core (Enhanced)",
        "version": "3.2.1",
        "status": "operational",
        "features": [
            "Comprehensive error handling",
            "Input validation",
            "Circuit breakers",
            "Retry mechanisms",
            "Health checks",
            "Rate limiting",
            "Request tracing"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "circuit_breakers": "/metrics/circuit-breakers"
        }
    }

# ===================================================================
# STARTUP MESSAGE
# ===================================================================

@app.on_event("startup")
async def startup_message():
    logger.info("=" * 80)
    logger.info("🌾 Sahool Geo-Core - Enhanced Version")
    logger.info("=" * 80)
    logger.info("✅ Error handling: ENABLED")
    logger.info("✅ Input validation: ENABLED")
    logger.info("✅ Circuit breakers: ENABLED")
    logger.info("✅ Retry mechanisms: ENABLED")
    logger.info("✅ Health checks: ENABLED")
    logger.info("✅ Rate limiting: ENABLED")
    logger.info("=" * 80)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )

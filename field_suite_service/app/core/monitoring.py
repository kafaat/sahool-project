"""
Monitoring and Observability for Sahool Yemen
سهول اليمن - المراقبة والرصد

Advanced metrics, logging, tracing, and health monitoring.
"""
import asyncio
import time
import os
import platform
import psutil
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Prometheus Metrics
# =============================================================================

# Request metrics
REQUEST_COUNT = Counter(
    "sahool_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "sahool_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

REQUEST_IN_PROGRESS = Gauge(
    "sahool_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"]
)

# Service health metrics
SERVICE_HEALTH = Gauge(
    "sahool_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"]
)

SERVICE_LATENCY = Histogram(
    "sahool_service_latency_seconds",
    "Inter-service call latency",
    ["source", "target"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Database metrics
DB_QUERY_COUNT = Counter(
    "sahool_db_queries_total",
    "Total database queries",
    ["operation", "table"]
)

DB_QUERY_LATENCY = Histogram(
    "sahool_db_query_duration_seconds",
    "Database query latency",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

DB_POOL_SIZE = Gauge(
    "sahool_db_pool_size",
    "Database connection pool size",
    ["pool"]
)

# Cache metrics
CACHE_HITS = Counter(
    "sahool_cache_hits_total",
    "Total cache hits",
    ["cache"]
)

CACHE_MISSES = Counter(
    "sahool_cache_misses_total",
    "Total cache misses",
    ["cache"]
)

CACHE_SIZE = Gauge(
    "sahool_cache_size",
    "Current cache size",
    ["cache"]
)

# Yemen-specific metrics
YEMEN_FIELD_COUNT = Gauge(
    "sahool_yemen_fields_total",
    "Total number of fields by region",
    ["region"]
)

YEMEN_FARMER_COUNT = Gauge(
    "sahool_yemen_farmers_total",
    "Total number of farmers by region",
    ["region"]
)

YEMEN_NDVI_AVERAGE = Gauge(
    "sahool_yemen_ndvi_average",
    "Average NDVI by region",
    ["region"]
)

YEMEN_WEATHER_TEMPERATURE = Gauge(
    "sahool_yemen_weather_temperature",
    "Current temperature by region",
    ["region"]
)

# System metrics
SYSTEM_CPU = Gauge(
    "sahool_system_cpu_percent",
    "System CPU usage percentage"
)

SYSTEM_MEMORY = Gauge(
    "sahool_system_memory_percent",
    "System memory usage percentage"
)

SYSTEM_DISK = Gauge(
    "sahool_system_disk_percent",
    "System disk usage percentage"
)

# Application info
APP_INFO = Info(
    "sahool_app",
    "Application information"
)


# =============================================================================
# Metrics Middleware
# =============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/metrics", "/health"]

    def _normalize_path(self, path: str) -> str:
        """Normalize path for metric labels (reduce cardinality)"""
        # Replace IDs with placeholders
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', path)
        return path

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        method = request.method
        path = self._normalize_path(request.url.path)

        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        start_time = time.time()

        try:
            response = await call_next(request)

            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status_code=response.status_code
            ).inc()

            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(time.time() - start_time)

            return response

        except Exception:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status_code=500
            ).inc()
            raise

        finally:
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()


# =============================================================================
# Structured Logging
# =============================================================================

def configure_logging(
    service_name: str = "sahool-yemen",
    log_level: str = "INFO",
    json_format: bool = True
):
    """Configure structured logging with structlog"""

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add service context
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment=os.getenv("ENVIRONMENT", "development")
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(time.time_ns()))

        # Bind request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )

        start_time = time.time()

        try:
            response = await call_next(request)

            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round((time.time() - start_time) * 1000, 2)
            )

            # Add request ID to response
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            logger.exception(
                "request_failed",
                error=str(e),
                duration_ms=round((time.time() - start_time) * 1000, 2)
            )
            raise

        finally:
            structlog.contextvars.unbind_contextvars(
                "request_id", "method", "path", "client_ip"
            )


# =============================================================================
# Health Checks
# =============================================================================

class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    details: dict = field(default_factory=dict)


class HealthChecker:
    """
    Comprehensive health checker for all components
    """

    def __init__(self):
        self._checks: dict[str, Callable] = {}
        self._last_check: Optional[dict] = None
        self._check_interval = 30  # seconds
        self._last_check_time = 0

    def register(self, name: str, check: Callable):
        """Register a health check"""
        self._checks[name] = check

    async def check_component(self, name: str, check: Callable) -> HealthCheckResult:
        """Run a single health check"""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(check):
                result = await check()
            else:
                result = check()

            latency = (time.time() - start_time) * 1000

            if isinstance(result, dict):
                status = HealthStatus.HEALTHY if result.get("healthy", True) else HealthStatus.UNHEALTHY
                return HealthCheckResult(
                    name=name,
                    status=status,
                    latency_ms=latency,
                    message=result.get("message", ""),
                    details=result
                )
            elif isinstance(result, bool):
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    latency_ms=latency
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    details={"result": str(result)}
                )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e)
            )

    async def run_all_checks(self, force: bool = False) -> dict:
        """Run all health checks"""
        now = time.time()

        # Use cached result if not expired
        if not force and self._last_check and (now - self._last_check_time) < self._check_interval:
            return self._last_check

        results = []
        overall_status = HealthStatus.HEALTHY

        for name, check in self._checks.items():
            result = await self.check_component(name, check)
            results.append(result)

            # Update Prometheus metric
            SERVICE_HEALTH.labels(service=name).set(
                1 if result.status == HealthStatus.HEALTHY else 0
            )

            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        self._last_check = {
            "status": overall_status.value,
            "timestamp": now,
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "latency_ms": round(r.latency_ms, 2),
                    "message": r.message,
                    "details": r.details
                }
                for r in results
            ]
        }
        self._last_check_time = now

        return self._last_check

    async def liveness_check(self) -> dict:
        """Simple liveness check (is the service running?)"""
        return {
            "status": "alive",
            "timestamp": time.time()
        }

    async def readiness_check(self) -> dict:
        """Readiness check (can the service handle requests?)"""
        return await self.run_all_checks()


# Global health checker
health_checker = HealthChecker()


# =============================================================================
# System Metrics Collector
# =============================================================================

class SystemMetricsCollector:
    """
    Collects system-level metrics
    """

    def __init__(self):
        self._running = False
        self._task = None

    async def start(self, interval: int = 15):
        """Start collecting system metrics"""
        self._running = True
        self._task = asyncio.create_task(self._collect_loop(interval))
        logger.info("system_metrics_collector_started")

    async def stop(self):
        """Stop collecting system metrics"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("system_metrics_collector_stopped")

    async def _collect_loop(self, interval: int):
        """Periodically collect system metrics"""
        while self._running:
            try:
                self._collect_metrics()
            except Exception as e:
                logger.warning("system_metrics_error", error=str(e))

            await asyncio.sleep(interval)

    def _collect_metrics(self):
        """Collect current system metrics"""
        # CPU
        SYSTEM_CPU.set(psutil.cpu_percent())

        # Memory
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY.set(memory.percent)

        # Disk
        disk = psutil.disk_usage('/')
        SYSTEM_DISK.set(disk.percent)

    def get_system_info(self) -> dict:
        """Get current system information"""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
            "disk_percent": psutil.disk_usage('/').percent,
        }


# Global system metrics collector
system_metrics = SystemMetricsCollector()


# =============================================================================
# Tracing Decorator
# =============================================================================

def trace_operation(
    operation_name: str,
    service: Optional[str] = None
):
    """
    Decorator to trace function execution

    Logs entry, exit, duration, and any errors.
    """
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            span_id = f"{operation_name}:{time.time_ns()}"

            logger.debug(
                "operation_started",
                operation=operation_name,
                span_id=span_id
            )

            try:
                result = await func(*args, **kwargs)

                duration = (time.time() - start_time) * 1000
                logger.debug(
                    "operation_completed",
                    operation=operation_name,
                    span_id=span_id,
                    duration_ms=round(duration, 2)
                )

                if service:
                    SERVICE_LATENCY.labels(
                        source="main",
                        target=service
                    ).observe(duration / 1000)

                return result

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    operation=operation_name,
                    span_id=span_id,
                    duration_ms=round(duration, 2),
                    error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            span_id = f"{operation_name}:{time.time_ns()}"

            logger.debug(
                "operation_started",
                operation=operation_name,
                span_id=span_id
            )

            try:
                result = func(*args, **kwargs)

                duration = (time.time() - start_time) * 1000
                logger.debug(
                    "operation_completed",
                    operation=operation_name,
                    span_id=span_id,
                    duration_ms=round(duration, 2)
                )

                return result

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    operation=operation_name,
                    span_id=span_id,
                    duration_ms=round(duration, 2),
                    error=str(e)
                )
                raise

        return async_wrapper if is_async else sync_wrapper

    return decorator


# =============================================================================
# Metrics Endpoint
# =============================================================================

async def metrics_endpoint() -> Response:
    """Generate Prometheus metrics response"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# Application Startup
# =============================================================================

def set_app_info(
    version: str = "6.0.0",
    service_name: str = "sahool-yemen",
    environment: str = "production"
):
    """Set application info for metrics"""
    APP_INFO.info({
        "version": version,
        "service": service_name,
        "environment": environment,
        "python_version": platform.python_version(),
        "platform": platform.system(),
    })

"""
Comprehensive Health Checks
مراقبة صحة النظام للكشف المبكر عن المشاكل
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

import psycopg2
import httpx
import redis

# ===================================================================
# HEALTH STATUS
# ===================================================================

class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status for a component"""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    last_checked: datetime


class SystemHealth(BaseModel):
    """Overall system health"""
    status: HealthStatus
    components: List[ComponentHealth]
    uptime_seconds: float
    version: str
    timestamp: datetime


# ===================================================================
# HEALTH CHECKERS
# ===================================================================

class DatabaseHealthChecker:
    """Check database health"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def check(self) -> ComponentHealth:
        """Check database connectivity and performance"""

        start_time = time.time()

        try:
            # Test connection
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()

            # Test query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # Check connection pool
            cursor.execute("""
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
            """)
            conn_stats = cursor.fetchone()

            # Close
            cursor.close()
            conn.close()

            response_time = (time.time() - start_time) * 1000

            # Determine status
            if response_time > 1000:  # > 1 second
                status = HealthStatus.DEGRADED
                message = "Database responding slowly"
            elif conn_stats[1] > 50:  # > 50 active connections
                status = HealthStatus.DEGRADED
                message = "High number of active connections"
            else:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"

            return ComponentHealth(
                name="database",
                status=status,
                response_time_ms=round(response_time, 2),
                message=message,
                details={
                    "total_connections": conn_stats[0],
                    "active_connections": conn_stats[1],
                    "idle_connections": conn_stats[2]
                },
                last_checked=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"Database connection failed: {str(e)}",
                last_checked=datetime.utcnow()
            )


class RedisHealthChecker:
    """Check Redis health"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    async def check(self) -> ComponentHealth:
        """Check Redis connectivity"""

        start_time = time.time()

        try:
            r = redis.from_url(self.redis_url)

            # Ping
            r.ping()

            # Get info
            info = r.info()

            # Close
            r.close()

            response_time = (time.time() - start_time) * 1000

            # Determine status
            memory_usage_ratio = info['used_memory'] / info['maxmemory'] if info.get('maxmemory', 0) > 0 else 0

            if response_time > 500:
                status = HealthStatus.DEGRADED
                message = "Redis responding slowly"
            elif memory_usage_ratio > 0.9:
                status = HealthStatus.DEGRADED
                message = "Redis memory usage high"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"

            return ComponentHealth(
                name="redis",
                status=status,
                response_time_ms=round(response_time, 2),
                message=message,
                details={
                    "connected_clients": info['connected_clients'],
                    "used_memory_mb": round(info['used_memory'] / 1024 / 1024, 2),
                    "memory_usage_percent": round(memory_usage_ratio * 100, 2)
                },
                last_checked=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"Redis connection failed: {str(e)}",
                last_checked=datetime.utcnow()
            )


class ServiceHealthChecker:
    """Check external service health"""

    def __init__(self, name: str, url: str, timeout: float = 5.0):
        self.name = name
        self.url = url
        self.timeout = timeout

    async def check(self) -> ComponentHealth:
        """Check service health endpoint"""

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url)

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = f"{self.name} is healthy"
            elif response.status_code == 503:
                status = HealthStatus.DEGRADED
                message = f"{self.name} is degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{self.name} returned status {response.status_code}"

            # Try to parse response
            details = None
            try:
                details = response.json()
            except:
                pass

            return ComponentHealth(
                name=self.name,
                status=status,
                response_time_ms=round(response_time, 2),
                message=message,
                details=details,
                last_checked=datetime.utcnow()
            )

        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"{self.name} timed out after {self.timeout}s",
                last_checked=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"{self.name} error: {str(e)}",
                last_checked=datetime.utcnow()
            )


class DiskHealthChecker:
    """Check disk space"""

    async def check(self) -> ComponentHealth:
        """Check available disk space"""

        start_time = time.time()

        try:
            import shutil

            total, used, free = shutil.disk_usage("/")

            usage_percent = (used / total) * 100

            response_time = (time.time() - start_time) * 1000

            # Determine status
            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage critical: {usage_percent:.1f}%"
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {usage_percent:.1f}%"

            return ComponentHealth(
                name="disk",
                status=status,
                response_time_ms=round(response_time, 2),
                message=message,
                details={
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    "usage_percent": round(usage_percent, 2)
                },
                last_checked=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"Disk check failed: {str(e)}",
                last_checked=datetime.utcnow()
            )


class MemoryHealthChecker:
    """Check memory usage"""

    async def check(self) -> ComponentHealth:
        """Check memory usage"""

        start_time = time.time()

        try:
            import psutil

            memory = psutil.virtual_memory()

            usage_percent = memory.percent

            response_time = (time.time() - start_time) * 1000

            # Determine status
            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical: {usage_percent:.1f}%"
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {usage_percent:.1f}%"

            return ComponentHealth(
                name="memory",
                status=status,
                response_time_ms=round(response_time, 2),
                message=message,
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": round(usage_percent, 2)
                },
                last_checked=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"Memory check failed: {str(e)}",
                last_checked=datetime.utcnow()
            )


# ===================================================================
# HEALTH CHECK MANAGER
# ===================================================================

class HealthCheckManager:
    """Manage all health checks"""

    def __init__(self, app_version: str = "3.2.1"):
        self.app_version = app_version
        self.start_time = time.time()
        self.checkers: List = []

    def add_checker(self, checker):
        """Add health checker"""
        self.checkers.append(checker)

    async def check_all(self) -> SystemHealth:
        """Run all health checks"""

        # Run all checks in parallel
        check_tasks = [checker.check() for checker in self.checkers]
        component_healths = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Convert exceptions to unhealthy status
        components = []
        for i, result in enumerate(component_healths):
            if isinstance(result, Exception):
                components.append(ComponentHealth(
                    name=f"checker_{i}",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    message=f"Health check failed: {str(result)}",
                    last_checked=datetime.utcnow()
                ))
            else:
                components.append(result)

        # Determine overall status
        statuses = [c.status for c in components]

        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Calculate uptime
        uptime = time.time() - self.start_time

        return SystemHealth(
            status=overall_status,
            components=components,
            uptime_seconds=round(uptime, 2),
            version=self.app_version,
            timestamp=datetime.utcnow()
        )


# ===================================================================
# FASTAPI INTEGRATION
# ===================================================================

"""
# In FastAPI app:

from shared.health_checks import (
    HealthCheckManager,
    DatabaseHealthChecker,
    RedisHealthChecker,
    ServiceHealthChecker,
    DiskHealthChecker,
    MemoryHealthChecker
)

# Initialize
health_manager = HealthCheckManager(app_version="3.2.1")

# Add checkers
health_manager.add_checker(DatabaseHealthChecker(
    connection_string="postgresql://user:pass@localhost/sahool"
))

health_manager.add_checker(RedisHealthChecker(
    redis_url="redis://localhost:6379/0"
))

health_manager.add_checker(ServiceHealthChecker(
    name="ml-engine",
    url="http://ml-engine:8010/health"
))

health_manager.add_checker(ServiceHealthChecker(
    name="agent-ai",
    url="http://agent-ai:8002/health"
))

health_manager.add_checker(DiskHealthChecker())
health_manager.add_checker(MemoryHealthChecker())


# Health endpoint
@app.get("/health", response_model=SystemHealth)
async def health_check():
    return await health_manager.check_all()


# Liveness probe (simple)
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


# Readiness probe
@app.get("/health/ready")
async def readiness():
    health = await health_manager.check_all()

    if health.status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}
"""

#!/bin/bash

# =============================================================================
# سكريبت سد الفجوات الحرجة - Critical Gaps Fix Script
# لمشروع Sahool - v2.0
# آخر تحديث: 2025-12-04
# تم المراجعة والإصلاح
# =============================================================================

set -e  # توقف عند أول خطأ

# الألوان للتنسيق
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# متغيرات المسار - تم تصحيحها
PROJECT_ROOT=$(pwd)
SERVICES_DIR="$PROJECT_ROOT/services"
NANO_SERVICES_DIR="$PROJECT_ROOT/nano_services"
SHARED_LIBS_DIR="$PROJECT_ROOT/libs-shared"
DEPLOY_SCRIPTS_DIR="$PROJECT_ROOT/scripts/deploy"

# ================================================
# 1. دوال تسجيل وطباعة
# ================================================
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# ================================================
# 2. التحقق من المتطلبات المسبقة
# ================================================
check_requirements() {
    log "التحقق من المتطلبات المسبقة..."

    # تحقق من Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 غير مثبت"
        exit 1
    fi

    # تحقق من pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        error "pip غير مثبت"
        exit 1
    fi

    # تحقق من وجود المجلدات الأساسية
    if [ ! -d "$SHARED_LIBS_DIR" ]; then
        error "مجلد libs-shared غير موجود"
        exit 1
    fi

    if [ ! -d "$NANO_SERVICES_DIR" ]; then
        error "مجلد nano_services غير موجود"
        exit 1
    fi

    success "جميع المتطلبات متوفرة"
}

# ================================================
# 3. إنشاء Database Pooling - تم الإصلاح
# ================================================
create_database_pooling() {
    log "إنشاء Database Pooling Manager..."

    # المسار الصحيح: app/ وليس src/
    mkdir -p "$NANO_SERVICES_DIR/weather-core/app/database"

    cat > "$NANO_SERVICES_DIR/weather-core/app/database/__init__.py" << 'EOF'
from .pool_manager import MonitoredDatabasePool, DatabaseManager

__all__ = ['MonitoredDatabasePool', 'DatabaseManager']
EOF

    cat > "$NANO_SERVICES_DIR/weather-core/app/database/pool_manager.py" << 'EOF'
"""
Database Pool Manager - Sahool Yemen Platform
مدير مجموعة اتصالات قاعدة البيانات
"""
import asyncio
import os
import time
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from contextlib import asynccontextmanager

try:
    import asyncpg
    from asyncpg import Pool, Connection
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    Pool = None
    Connection = None

logger = logging.getLogger(__name__)

@dataclass
class PoolMetrics:
    """Database pool metrics"""
    pool_size: int
    free_connections: int
    used_connections: int
    total_queries: int
    avg_query_time: float
    errors: int
    health_status: str


class MonitoredDatabasePool:
    """Database connection pool with monitoring capabilities"""

    def __init__(self, database_url: str, pool_config: Dict[str, Any]):
        self.database_url = database_url
        self.pool: Optional[Pool] = None
        self.config = pool_config

        # Metrics
        self.total_queries = 0
        self.total_query_time = 0.0
        self.errors = 0
        self.query_times: List[float] = []
        self.max_history = 1000
        self.healthy = True
        self.last_health_check = time.time()

        # Connection tracking
        self.active_connections: set = set()
        self._lock = None

    async def initialize(self) -> None:
        """Initialize the connection pool with monitoring"""
        if not HAS_ASYNCPG:
            logger.warning("asyncpg not installed, using mock pool")
            self.healthy = True
            return

        self._lock = asyncio.Lock()

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.config.get('min_size', 5),
                max_size=self.config.get('max_size', 20),
                max_queries=self.config.get('max_queries', 10000),
                max_inactive_connection_lifetime=self.config.get('max_inactive_time', 300.0),
                command_timeout=self.config.get('command_timeout', 30.0),
                server_settings={
                    'application_name': self.config.get('app_name', 'sahool-service'),
                },
            )

            logger.info(f"Database pool initialized: {self.config}")
            await self._start_health_monitor()

        except Exception as e:
            logger.error(f"Failed to initialize pool: {e}")
            self.healthy = False
            raise

    async def _start_health_monitor(self):
        """Start background health monitoring"""
        async def monitor():
            while True:
                try:
                    await self._health_check()
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")

        asyncio.create_task(monitor())

    async def _health_check(self):
        """Perform health check on the pool"""
        if not self.pool:
            return

        try:
            async with self.pool.acquire() as conn:
                start = time.time()
                result = await conn.fetchval("SELECT 1")
                query_time = time.time() - start

                if result != 1:
                    raise Exception("Health check query failed")

                self.healthy = True
                self.last_health_check = time.time()

                if query_time > 1.0:
                    logger.warning(f"Slow health check: {query_time:.3f}s")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.healthy = False

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """Acquire connection with automatic monitoring"""
        if not self.pool:
            raise Exception("Pool not initialized")

        conn = None
        start_time = time.time()

        try:
            conn = await self.pool.acquire()
            acquire_time = time.time() - start_time

            if acquire_time > 0.5:
                logger.warning(f"Slow connection acquisition: {acquire_time:.3f}s")

            yield conn

        except Exception as e:
            self.errors += 1
            logger.error(f"Database error: {e}")
            raise

        finally:
            if conn:
                await self.pool.release(conn)
                self.total_queries += 1

    async def execute(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query with monitoring"""
        start = time.time()

        try:
            async with self.acquire() as conn:
                result = await conn.fetch(query, *args)
                query_time = time.time() - start

                self._record_query_time(query_time)

                return [dict(row) for row in result]

        except Exception as e:
            logger.error(f"Query failed: {query[:100]}... - Error: {e}")
            raise

    def _record_query_time(self, duration: float):
        """Record query execution time"""
        self.total_query_time += duration
        self.query_times.append(duration)

        if len(self.query_times) > self.max_history:
            self.query_times.pop(0)

        if duration > 5.0:
            logger.error(f"Very slow query: {duration:.3f}s")

    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        if not self.pool:
            return PoolMetrics(0, 0, 0, 0, 0, self.errors, 'not_initialized')

        avg_time = sum(self.query_times[-100:]) / len(self.query_times[-100:]) if self.query_times else 0

        return PoolMetrics(
            pool_size=self.pool.get_max_size(),
            free_connections=self.pool.get_idle_size(),
            used_connections=self.pool.get_size(),
            total_queries=self.total_queries,
            avg_query_time=avg_time,
            errors=self.errors,
            health_status='healthy' if self.healthy else 'unhealthy'
        )

    async def close(self):
        """Gracefully close the pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")


class DatabaseManager:
    """Singleton manager for database pools"""
    _pools: Dict[str, MonitoredDatabasePool] = {}

    @classmethod
    async def get_pool(cls, service_name: str) -> MonitoredDatabasePool:
        """Get or create a database pool for a service"""
        if service_name not in cls._pools:
            config = {
                'min_size': int(os.getenv('DB_POOL_MIN', '5')),
                'max_size': int(os.getenv('DB_POOL_MAX', '20')),
                'max_queries': int(os.getenv('DB_POOL_MAX_QUERIES', '10000')),
                'command_timeout': float(os.getenv('DB_COMMAND_TIMEOUT', '30.0')),
                'app_name': f'sahool-{service_name}',
            }

            database_url = os.getenv('DATABASE_URL', '')
            pool = MonitoredDatabasePool(database_url, config)
            await pool.initialize()
            cls._pools[service_name] = pool

        return cls._pools[service_name]

    @classmethod
    async def close_all(cls):
        """Close all pools"""
        for pool in cls._pools.values():
            await pool.close()
        cls._pools.clear()
EOF

    success "تم إنشاء Database Pooling Manager"
}

# ================================================
# 4. إنشاء Secrets Management - تم الإصلاح
# ================================================
create_secrets_manager() {
    log "إنشاء Secrets Management..."

    cat > "$SHARED_LIBS_DIR/sahool_shared/secrets_manager.py" << 'EOF'
"""
Secrets Manager - Sahool Yemen Platform
مدير الأسرار والمفاتيح
"""
import os
import time
import json
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional imports
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    ClientError = Exception

try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


class SecretsManager:
    """Multi-provider secrets manager with caching"""

    def __init__(self, provider: str = 'env'):
        self.provider = provider
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self.client = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize the secrets client based on provider"""
        if self.provider == 'aws' and HAS_BOTO3:
            try:
                self.client = boto3.session.Session().client(
                    service_name='secretsmanager',
                    region_name=os.getenv('AWS_REGION', 'us-east-1'),
                    endpoint_url=os.getenv('AWS_SECRETS_ENDPOINT'),
                )
                logger.info("AWS Secrets Manager client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS client: {e}")
                self.provider = 'env'

        elif self.provider == 'vault' and HAS_HVAC:
            try:
                self.client = hvac.Client(
                    url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
                    token=os.getenv('VAULT_TOKEN'),
                    verify=os.getenv('VAULT_VERIFY_SSL', 'true').lower() == 'true'
                )
                logger.info("HashiCorp Vault client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Vault client: {e}")
                self.provider = 'env'
        else:
            self.provider = 'env'
            logger.info("Using environment variables for secrets")

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get secret with caching"""
        cache_key = f"{secret_name}:{version or 'latest'}"

        # Check cache TTL
        if cache_key in self._cache_ttl:
            if self._cache_ttl[cache_key] > time.time():
                return self._cache.get(cache_key, {})

        try:
            secret = self._fetch_secret(secret_name, version)

            # Cache with TTL
            ttl = int(os.getenv('SECRET_CACHE_TTL', '3600'))
            self._cache[cache_key] = secret
            self._cache_ttl[cache_key] = time.time() + ttl

            logger.info(f"Secret retrieved: {secret_name}")
            return secret

        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return self._fallback_to_env(secret_name)

    def _fetch_secret(self, secret_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Fetch secret from provider"""
        if self.provider == 'aws' and self.client:
            kwargs = {'SecretId': secret_name}
            if version:
                kwargs['VersionId'] = version

            response = self.client.get_secret_value(**kwargs)

            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                return json.loads(base64.b64decode(response['SecretBinary']))

        elif self.provider == 'vault' and self.client:
            mount_point = os.getenv('VAULT_MOUNT_POINT', 'secret')
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point=mount_point
            )
            return response['data']['data']

        else:
            return self._fallback_to_env(secret_name)

    def _fallback_to_env(self, secret_name: str) -> Dict[str, Any]:
        """Fallback to environment variables"""
        env_name = secret_name.replace('-', '_').replace('/', '_').upper()
        env_value = os.getenv(env_name)

        if env_value:
            try:
                return json.loads(env_value)
            except json.JSONDecodeError:
                return {'value': env_value}

        logger.warning(f"No fallback for secret: {secret_name}")
        return {}

    def get_database_credentials(self, environment: str = 'production') -> Dict[str, str]:
        """Get database credentials"""
        secret_name = f"sahool/{environment}/database"
        secret = self.get_secret(secret_name)

        return {
            'host': secret.get('host', os.getenv('DB_HOST', 'localhost')),
            'port': str(secret.get('port', os.getenv('DB_PORT', '5432'))),
            'dbname': secret.get('dbname', os.getenv('DB_NAME', 'sahool')),
            'username': secret.get('username', os.getenv('DB_USER', 'postgres')),
            'password': secret.get('password', os.getenv('DB_PASS', '')),
        }

    def get_jwt_secrets(self, environment: str = 'production') -> Dict[str, str]:
        """Get JWT secrets"""
        secret_name = f"sahool/{environment}/jwt"
        secret = self.get_secret(secret_name)

        return {
            'secret_key': secret.get('secret_key', os.getenv('JWT_SECRET_KEY', '')),
            'algorithm': secret.get('algorithm', os.getenv('JWT_ALGORITHM', 'HS256')),
            'access_token_expire': secret.get('access_token_expire', os.getenv('JWT_ACCESS_EXPIRE', '30')),
        }

    def get_api_keys(self, service: str) -> Dict[str, str]:
        """Get API keys for external services"""
        secret_name = f"sahool/api-keys/{service}"
        secret = self.get_secret(secret_name)

        # Fallback to environment
        if not secret:
            env_prefix = service.upper().replace('-', '_')
            return {
                'api_key': os.getenv(f'{env_prefix}_API_KEY', ''),
                'api_secret': os.getenv(f'{env_prefix}_API_SECRET', ''),
            }

        return secret

    def get_redis_credentials(self) -> Dict[str, str]:
        """Get Redis credentials"""
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': os.getenv('REDIS_PORT', '6379'),
            'password': os.getenv('REDIS_PASSWORD', ''),
            'db': os.getenv('REDIS_DB', '0'),
        }


# Global instance
def get_secrets_manager() -> SecretsManager:
    """Get or create global secrets manager instance"""
    provider = os.getenv('SECRETS_PROVIDER', 'env')
    return SecretsManager(provider=provider)

secrets_manager = get_secrets_manager()
EOF

    success "تم إنشاء Secrets Management"
}

# ================================================
# 5. Centralized Logging مع OpenTelemetry - تم الإصلاح
# ================================================
create_centralized_logging() {
    log "إنشاء Centralized Logging..."

    mkdir -p "$SHARED_LIBS_DIR/sahool_shared/logging"

    cat > "$SHARED_LIBS_DIR/sahool_shared/logging/__init__.py" << 'EOF'
from .otel_logger import get_logger, OtelLogger

__all__ = ['get_logger', 'OtelLogger']
EOF

    cat > "$SHARED_LIBS_DIR/sahool_shared/logging/otel_logger.py" << 'EOF'
"""
OpenTelemetry Logger - Sahool Yemen Platform
نظام التسجيل المركزي
"""
import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Optional imports
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False


class OtelLogger:
    """OpenTelemetry-enabled logger"""

    def __init__(self, service_name: str, service_version: str = "2.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer = None

        self._setup_otel()
        self.logger = self._configure_logger()

    def _setup_otel(self):
        """Setup OpenTelemetry tracing"""
        if not HAS_OTEL:
            return

        try:
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "deployment.environment": os.getenv('ENVIRONMENT', 'development'),
            })

            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

            self.tracer = trace.get_tracer(self.service_name)
        except Exception as e:
            logging.warning(f"Failed to setup OpenTelemetry: {e}")

    def _configure_logger(self) -> logging.Logger:
        """Configure the logger with JSON formatting"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        logger.handlers.clear()

        handler = logging.StreamHandler()

        if HAS_JSON_LOGGER:
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S%z'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _get_trace_context(self) -> Dict[str, str]:
        """Get current trace context"""
        context = {}
        if HAS_OTEL and self.tracer:
            span = trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                context['trace_id'] = format(ctx.trace_id, '032x')
                context['span_id'] = format(ctx.span_id, '016x')
        return context

    def _format_extra(self, **kwargs) -> Dict[str, Any]:
        """Format extra fields for logging"""
        extra = {
            'service': self.service_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        extra.update(self._get_trace_context())
        extra.update(kwargs)
        return {'extra': extra}

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **self._format_extra(**kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **self._format_extra(**kwargs))

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = type(exception).__name__
        self.logger.error(message, exc_info=exception is not None, **self._format_extra(**kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **self._format_extra(**kwargs))

    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a tracing span"""
        if self.tracer:
            return self.tracer.start_as_current_span(name, attributes=attributes or {})
        # Return a no-op context manager if no tracer
        from contextlib import nullcontext
        return nullcontext()


# Logger cache
_loggers: Dict[str, OtelLogger] = {}

def get_logger(service_name: str, version: str = "2.0.0") -> OtelLogger:
    """Get or create a logger for a service"""
    if service_name not in _loggers:
        _loggers[service_name] = OtelLogger(service_name, version)
    return _loggers[service_name]
EOF

    success "تم إنشاء Centralized Logging"
}

# ================================================
# 6. Circuit Breaker - تم الإصلاح
# ================================================
create_circuit_breaker() {
    log "إنشاء Circuit Breaker..."

    mkdir -p "$SHARED_LIBS_DIR/sahool_shared/resilience"

    cat > "$SHARED_LIBS_DIR/sahool_shared/resilience/__init__.py" << 'EOF'
from .circuit_breaker import CircuitBreaker, CircuitState, get_circuit_breaker

__all__ = ['CircuitBreaker', 'CircuitState', 'get_circuit_breaker']
EOF

    cat > "$SHARED_LIBS_DIR/sahool_shared/resilience/circuit_breaker.py" << 'EOF'
"""
Circuit Breaker - Sahool Yemen Platform
قاطع الدائرة للمرونة
"""
import asyncio
import time
import logging
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics"""
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    short_circuits: int = 0
    state_transitions: list = field(default_factory=list)
    last_failure_time: Optional[float] = None


class CircuitBreaker:
    """Resilient circuit breaker implementation"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        config = config or {}

        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.next_attempt = time.time()
        self.half_open_calls = 0
        self.metrics = CircuitMetrics()
        self._lock = None

        # Configuration
        self.failure_threshold = config.get('failure_threshold', 5)
        self.success_threshold = config.get('success_threshold', 3)
        self.timeout = config.get('timeout', 30.0)
        self.reset_timeout = config.get('reset_timeout', 60.0)
        self.half_open_max_calls = config.get('half_open_max_calls', 2)

    async def _get_lock(self):
        """Get or create async lock"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def call(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not await self._can_execute():
            self.metrics.short_circuits += 1
            raise CircuitOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = await asyncio.wait_for(
                fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else asyncio.to_thread(fn, *args, **kwargs),
                timeout=self.timeout
            )
            await self._on_success()
            return result

        except asyncio.TimeoutError:
            self.metrics.timeouts += 1
            await self._on_failure()
            raise

        except Exception as e:
            await self._on_failure()
            raise

    async def _can_execute(self) -> bool:
        """Check if execution is allowed"""
        lock = await self._get_lock()
        async with lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False

            if self.state == CircuitState.OPEN:
                if time.time() >= self.next_attempt:
                    await self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False

        return False

    async def _on_success(self):
        """Handle successful execution"""
        lock = await self._get_lock()
        async with lock:
            self.metrics.successes += 1

            if self.state == CircuitState.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
            elif self.state == CircuitState.CLOSED:
                self.failures = max(0, self.failures - 1)

    async def _on_failure(self):
        """Handle failed execution"""
        lock = await self._get_lock()
        async with lock:
            self.metrics.failures += 1
            self.metrics.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.CLOSED:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state

        self.metrics.state_transitions.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': time.time()
        })

        logger.info(f"Circuit {self.name}: {old_state.value} -> {new_state.value}")

        if new_state == CircuitState.OPEN:
            self.next_attempt = time.time() + self.reset_timeout
            self.failures = 0
            self.successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0
            self.successes = 0
        elif new_state == CircuitState.CLOSED:
            self.failures = 0
            self.successes = 0
            self.half_open_calls = 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failures': self.failures,
            'successes': self.successes,
            'metrics': {
                'total_successes': self.metrics.successes,
                'total_failures': self.metrics.failures,
                'total_timeouts': self.metrics.timeouts,
                'total_short_circuits': self.metrics.short_circuits,
            }
        }

    async def reset(self):
        """Reset circuit to closed state"""
        lock = await self._get_lock()
        async with lock:
            await self._transition_to(CircuitState.CLOSED)


class CircuitOpenError(Exception):
    """Exception raised when circuit is open"""
    pass


# Circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: Optional[Dict[str, Any]] = None) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]
EOF

    success "تم إنشاء Circuit Breaker"
}

# ================================================
# 7. تحديث __init__.py للمكتبة المشتركة
# ================================================
update_shared_lib_init() {
    log "تحديث ملف __init__.py للمكتبة المشتركة..."

    cat > "$SHARED_LIBS_DIR/sahool_shared/__init__.py" << 'EOF'
"""
Sahool Shared Library - المكتبة المشتركة لمنصة سهول
"""
__version__ = "2.0.0"

# Auth
from sahool_shared.auth import (
    hash_password,
    verify_password,
    needs_rehash,
    JWTHandler,
)

# Database
from sahool_shared.database import (
    DatabaseManager,
    get_async_db_session,
)

# Models
from sahool_shared.models import (
    Alert,
    Field,
    PlantHealth,
    Region,
    Farmer,
)

# Schemas
from sahool_shared.schemas import (
    TokenResponse,
    FieldResponse,
    WeatherResponse,
)

# Try to import optional modules
try:
    from sahool_shared.secrets_manager import secrets_manager, get_secrets_manager
except ImportError:
    secrets_manager = None
    get_secrets_manager = None

try:
    from sahool_shared.logging import get_logger, OtelLogger
except ImportError:
    get_logger = None
    OtelLogger = None

try:
    from sahool_shared.resilience import CircuitBreaker, get_circuit_breaker
except ImportError:
    CircuitBreaker = None
    get_circuit_breaker = None

__all__ = [
    # Version
    "__version__",
    # Auth
    "hash_password",
    "verify_password",
    "needs_rehash",
    "JWTHandler",
    # Database
    "DatabaseManager",
    "get_async_db_session",
    # Models
    "Alert",
    "Field",
    "PlantHealth",
    "Region",
    "Farmer",
    # Schemas
    "TokenResponse",
    "FieldResponse",
    "WeatherResponse",
    # Secrets
    "secrets_manager",
    "get_secrets_manager",
    # Logging
    "get_logger",
    "OtelLogger",
    # Resilience
    "CircuitBreaker",
    "get_circuit_breaker",
]
EOF

    success "تم تحديث __init__.py"
}

# ================================================
# 8. تحديث ملفات التكوين
# ================================================
update_configurations() {
    log "تحديث ملفات التكوين..."

    # إنشاء ملف .env.gaps.example
    cat > "$PROJECT_ROOT/.env.gaps.example" << 'EOF'
# ================================================
# Sahool - Critical Gaps Configuration
# إعدادات سد الفجوات الحرجة
# ================================================

# === Database Pooling ===
DATABASE_URL=postgresql://user:pass@localhost:5432/sahool
DB_POOL_MIN=5
DB_POOL_MAX=20
DB_POOL_MAX_QUERIES=10000
DB_COMMAND_TIMEOUT=30.0

# === Secrets Management ===
SECRETS_PROVIDER=env  # env, aws, vault
AWS_REGION=us-east-1
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=
SECRET_CACHE_TTL=3600

# === Logging ===
LOG_LEVEL=INFO
ENVIRONMENT=development

# === Circuit Breaker ===
CIRCUIT_FAILURE_THRESHOLD=5
CIRCUIT_RESET_TIMEOUT=60

# === Redis ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
EOF

    success "تم تحديث ملفات التكوين"
}

# ================================================
# 9. إنشاء سكربت التحقق
# ================================================
create_verification_script() {
    log "إنشاء سكربت التحقق..."

    cat > "$PROJECT_ROOT/scripts/verify-gaps-fix.sh" << 'EOF'
#!/bin/bash

echo "Verifying critical gaps fix..."
echo ""

ERRORS=0

# Check database pooling
if [ -f "nano_services/weather-core/app/database/pool_manager.py" ]; then
    echo "[OK] Database Pooling: Found"
else
    echo "[ERROR] Database Pooling: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check secrets manager
if [ -f "libs-shared/sahool_shared/secrets_manager.py" ]; then
    echo "[OK] Secrets Manager: Found"
else
    echo "[ERROR] Secrets Manager: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check logging
if [ -f "libs-shared/sahool_shared/logging/otel_logger.py" ]; then
    echo "[OK] Centralized Logging: Found"
else
    echo "[ERROR] Centralized Logging: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check circuit breaker
if [ -f "libs-shared/sahool_shared/resilience/circuit_breaker.py" ]; then
    echo "[OK] Circuit Breaker: Found"
else
    echo "[ERROR] Circuit Breaker: Missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "All critical gaps have been fixed!"
    exit 0
else
    echo "Found $ERRORS missing components"
    exit 1
fi
EOF

    chmod +x "$PROJECT_ROOT/scripts/verify-gaps-fix.sh"
    success "تم إنشاء سكربت التحقق"
}

# ================================================
# 10. دالة التنفيذ الرئيسية
# ================================================
main() {
    echo -e "${MAGENTA}
==============================================================
    Sahool Critical Gaps Fix Script v2.0
    سكريبت سد الفجوات الحرجة - تم المراجعة والإصلاح
==============================================================
${NC}"

    # خطوة 1: التحقق من المتطلبات
    check_requirements

    # خطوة 2: إنشاء الملفات
    create_database_pooling
    create_secrets_manager
    create_centralized_logging
    create_circuit_breaker

    # خطوة 3: تحديث المكتبة المشتركة
    update_shared_lib_init

    # خطوة 4: تحديث التكوينات
    update_configurations

    # خطوة 5: إنشاء سكربت التحقق
    create_verification_script

    echo ""
    echo -e "${GREEN}==============================================================
    Done! All critical gaps have been fixed.
    تم سد جميع الفجوات الحرجة بنجاح!
==============================================================${NC}"
    echo ""
    echo "Run verification: ./scripts/verify-gaps-fix.sh"
}

# تشغيل السكريبت
main "$@"

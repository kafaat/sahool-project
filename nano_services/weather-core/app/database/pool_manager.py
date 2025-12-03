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

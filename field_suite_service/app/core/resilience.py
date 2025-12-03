"""
Resilience Patterns for Sahool Yemen
سهول اليمن - أنماط المرونة والاستقرار

Circuit Breaker, Retry Logic, and Fault Tolerance
"""
import asyncio
import time
from enum import Enum
from typing import TypeVar, Callable, Any, Optional
from dataclasses import dataclass, field
from functools import wraps
import structlog
from collections import deque

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 30.0               # Seconds before trying half-open
    half_open_max_calls: int = 3        # Max calls in half-open state


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    total_failures: int = 0
    total_successes: int = 0
    half_open_calls: int = 0


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation

    Prevents cascade failures by stopping requests to failing services.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self.stats.state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open"""
        if self.stats.state != CircuitState.OPEN:
            return False
        elapsed = time.time() - self.stats.last_failure_time
        return elapsed >= self.config.timeout

    async def _update_state(self):
        """Update circuit state based on current conditions"""
        if self.stats.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.half_open_calls = 0
                self.stats.success_count = 0
                logger.info(
                    "circuit_half_open",
                    circuit=self.name,
                    message="Circuit transitioning to half-open"
                )

    async def record_success(self):
        """Record a successful call"""
        async with self._lock:
            self.stats.total_successes += 1

            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                if self.stats.success_count >= self.config.success_threshold:
                    self.stats.state = CircuitState.CLOSED
                    self.stats.failure_count = 0
                    logger.info(
                        "circuit_closed",
                        circuit=self.name,
                        message="Circuit closed after recovery"
                    )
            elif self.stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.stats.failure_count = max(0, self.stats.failure_count - 1)

    async def record_failure(self):
        """Record a failed call"""
        async with self._lock:
            self.stats.total_failures += 1
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            if self.stats.state == CircuitState.HALF_OPEN:
                # Immediate return to open on failure in half-open
                self.stats.state = CircuitState.OPEN
                logger.warning(
                    "circuit_reopened",
                    circuit=self.name,
                    message="Circuit reopened after half-open failure"
                )
            elif self.stats.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self.stats.state = CircuitState.OPEN
                    logger.error(
                        "circuit_opened",
                        circuit=self.name,
                        failures=self.stats.failure_count,
                        message="Circuit opened due to failures"
                    )

    async def can_execute(self) -> bool:
        """Check if a call can be executed"""
        async with self._lock:
            await self._update_state()

            if self.stats.state == CircuitState.CLOSED:
                return True

            if self.stats.state == CircuitState.OPEN:
                return False

            # Half-open: allow limited calls
            if self.stats.half_open_calls < self.config.half_open_max_calls:
                self.stats.half_open_calls += 1
                return True

            return False

    def get_stats(self) -> dict:
        """Get current circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    _instance: Optional['CircuitBreakerRegistry'] = None
    _breakers: dict[str, CircuitBreaker] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._breakers = {}
        return cls._instance

    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get_all_stats(self) -> list[dict]:
        """Get stats for all circuit breakers"""
        return [cb.get_stats() for cb in self._breakers.values()]


# Global registry instance
circuit_registry = CircuitBreakerRegistry()


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0         # Base delay in seconds
    max_delay: float = 30.0         # Maximum delay
    exponential_base: float = 2.0   # Exponential backoff base
    jitter: bool = True             # Add random jitter
    retryable_exceptions: tuple = (Exception,)


class RetryHandler:
    """
    Retry Handler with Exponential Backoff

    Automatically retries failed operations with configurable backoff.
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt"""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )

        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    async def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            except self.config.retryable_exceptions as e:
                last_exception = e

                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        "retry_attempt",
                        attempt=attempt + 1,
                        max_attempts=self.config.max_attempts,
                        delay=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "retry_exhausted",
                        attempts=self.config.max_attempts,
                        error=str(e)
                    )

        raise last_exception


def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to add circuit breaker to async function"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb = circuit_registry.get_or_create(name, config)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not await cb.can_execute():
                raise CircuitOpenError(f"Circuit '{name}' is open")

            try:
                result = await func(*args, **kwargs)
                await cb.record_success()
                return result
            except Exception as e:
                await cb.record_failure()
                raise

        return wrapper
    return decorator


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator to add retry logic to async function"""
    handler = RetryHandler(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# =============================================================================
# Rate Limiter
# =============================================================================

@dataclass
class RateLimiterConfig:
    """Configuration for rate limiter"""
    requests_per_second: float = 100.0
    burst_size: int = 20
    key_prefix: str = "rate_limit"


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter

    Controls request rate with burst allowance.
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()
        self._buckets: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default") -> bool:
        """Try to acquire a token"""
        async with self._lock:
            now = time.time()

            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": self.config.burst_size,
                    "last_update": now
                }

            bucket = self._buckets[key]

            # Refill tokens
            elapsed = now - bucket["last_update"]
            new_tokens = elapsed * self.config.requests_per_second
            bucket["tokens"] = min(
                self.config.burst_size,
                bucket["tokens"] + new_tokens
            )
            bucket["last_update"] = now

            # Try to consume
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True

            return False

    async def get_wait_time(self, key: str = "default") -> float:
        """Get time to wait before next token available"""
        async with self._lock:
            if key not in self._buckets:
                return 0.0

            bucket = self._buckets[key]
            if bucket["tokens"] >= 1:
                return 0.0

            tokens_needed = 1 - bucket["tokens"]
            return tokens_needed / self.config.requests_per_second


# =============================================================================
# Bulkhead Pattern
# =============================================================================

class Bulkhead:
    """
    Bulkhead Pattern Implementation

    Limits concurrent executions to prevent resource exhaustion.
    """

    def __init__(self, name: str, max_concurrent: int = 10, max_wait: float = 5.0):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_wait = max_wait
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0
        self._rejected = 0

    async def __aenter__(self):
        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.max_wait
            )
            if acquired:
                self._active += 1
                return self
        except asyncio.TimeoutError:
            self._rejected += 1
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full (max: {self.max_concurrent})"
            )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._active -= 1
        self._semaphore.release()
        return False

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active": self._active,
            "available": self.max_concurrent - self._active,
            "rejected": self._rejected,
        }


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity"""
    pass


# =============================================================================
# Health Check Aggregator
# =============================================================================

@dataclass
class HealthStatus:
    """Health status for a component"""
    name: str
    healthy: bool
    latency_ms: float = 0.0
    message: str = ""
    details: dict = field(default_factory=dict)


class HealthAggregator:
    """
    Aggregates health status from multiple components
    """

    def __init__(self):
        self._checks: dict[str, Callable] = {}

    def register(self, name: str, check: Callable):
        """Register a health check function"""
        self._checks[name] = check

    async def check_all(self) -> dict:
        """Run all health checks and aggregate results"""
        results = []
        overall_healthy = True

        for name, check in self._checks.items():
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(check):
                    result = await check()
                else:
                    result = check()

                latency = (time.time() - start) * 1000
                healthy = result.get("healthy", True) if isinstance(result, dict) else bool(result)

                results.append(HealthStatus(
                    name=name,
                    healthy=healthy,
                    latency_ms=latency,
                    details=result if isinstance(result, dict) else {}
                ))

                if not healthy:
                    overall_healthy = False

            except Exception as e:
                latency = (time.time() - start) * 1000
                results.append(HealthStatus(
                    name=name,
                    healthy=False,
                    latency_ms=latency,
                    message=str(e)
                ))
                overall_healthy = False

        return {
            "healthy": overall_healthy,
            "components": [
                {
                    "name": r.name,
                    "healthy": r.healthy,
                    "latency_ms": round(r.latency_ms, 2),
                    "message": r.message,
                    "details": r.details,
                }
                for r in results
            ]
        }


# Global health aggregator
health_aggregator = HealthAggregator()

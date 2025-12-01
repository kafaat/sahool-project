"""
Resilience Patterns: Retry, Circuit Breaker, Timeout
تقليل الأخطاء من خلال آليات المرونة والاستعادة التلقائية
"""
import asyncio
import time
import logging
from typing import Callable, Any, Optional, TypeVar, Generic
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ===================================================================
# RETRY MECHANISM
# ===================================================================

class RetryStrategy(str, Enum):
    """Retry strategies"""
    EXPONENTIAL = "exponential"  # 1s, 2s, 4s, 8s, ...
    LINEAR = "linear"            # 1s, 2s, 3s, 4s, ...
    FIXED = "fixed"              # 1s, 1s, 1s, 1s, ...


class RetryConfig:
    """Retry configuration"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        backoff_multiplier: float = 2.0,
        retry_on: tuple = (Exception,),  # Exceptions to retry on
        dont_retry_on: tuple = ()        # Exceptions to NOT retry
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.backoff_multiplier = backoff_multiplier
        self.retry_on = retry_on
        self.dont_retry_on = dont_retry_on

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""

        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        else:  # FIXED
            delay = self.initial_delay

        return min(delay, self.max_delay)


def retry_async(config: Optional[RetryConfig] = None):
    """Decorator for async functions with retry logic"""

    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result

                except config.dont_retry_on as e:
                    # Don't retry these exceptions
                    logger.warning(f"❌ {func.__name__}: Non-retryable error: {e}")
                    raise

                except config.retry_on as e:
                    last_exception = e

                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"🔄 {func.__name__}: Attempt {attempt}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"❌ {func.__name__}: All {config.max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )

            # All attempts failed
            raise last_exception

        return wrapper

    return decorator


def retry_sync(config: Optional[RetryConfig] = None):
    """Decorator for sync functions with retry logic"""

    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    return result

                except config.dont_retry_on as e:
                    logger.warning(f"❌ {func.__name__}: Non-retryable error: {e}")
                    raise

                except config.retry_on as e:
                    last_exception = e

                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"🔄 {func.__name__}: Attempt {attempt}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ {func.__name__}: All {config.max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


# ===================================================================
# CIRCUIT BREAKER
# ===================================================================

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open"""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,          # Failures before opening
        success_threshold: int = 2,          # Successes before closing
        timeout: float = 60.0,               # Seconds to wait before half-open
        expected_exceptions: tuple = (Exception,)  # Exceptions to count as failures
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._call_history = deque(maxlen=100)  # Last 100 calls

    @property
    def state(self) -> CircuitState:
        """Get current state"""

        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    logger.info(f"🔄 Circuit breaker '{self.name}': Transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0

        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""

        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"⭕ Circuit breaker '{self.name}': OPEN - Rejecting call")
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable."
            )

        try:
            result = func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except self.expected_exceptions as e:
            # Failure
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function through circuit breaker"""

        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"⭕ Circuit breaker '{self.name}': OPEN - Rejecting call")
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable."
            )

        try:
            result = await func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except self.expected_exceptions as e:
            # Failure
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""

        self._call_history.append({
            "time": datetime.utcnow(),
            "success": True
        })

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            if self._success_count >= self.success_threshold:
                logger.info(f"✅ Circuit breaker '{self.name}': Closing (recovered)")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0

    def _on_failure(self):
        """Handle failed call"""

        self._call_history.append({
            "time": datetime.utcnow(),
            "success": False
        })

        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()

        if self._state == CircuitState.HALF_OPEN:
            # Back to OPEN
            logger.warning(f"⭕ Circuit breaker '{self.name}': Re-opening (still failing)")
            self._state = CircuitState.OPEN
            self._success_count = 0

        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                logger.error(
                    f"⭕ Circuit breaker '{self.name}': Opening "
                    f"({self._failure_count} failures)"
                )
                self._state = CircuitState.OPEN

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""

        recent_calls = list(self._call_history)
        total_calls = len(recent_calls)

        if total_calls == 0:
            success_rate = 0.0
        else:
            successful_calls = sum(1 for call in recent_calls if call["success"])
            success_rate = (successful_calls / total_calls) * 100

        return {
            "name": self.name,
            "state": self._state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "recent_calls": total_calls,
            "success_rate": round(success_rate, 2),
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None
        }


def circuit_breaker(breaker: CircuitBreaker):
    """Decorator for circuit breaker"""

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)

            return sync_wrapper

    return decorator


# ===================================================================
# TIMEOUT
# ===================================================================

class TimeoutError(Exception):
    """Timeout error"""
    pass


def timeout(seconds: float):
    """Decorator for timeout"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Function '{func.__name__}' timed out after {seconds}s"
                )

        return wrapper

    return decorator


# ===================================================================
# COMBINED RESILIENCE DECORATOR
# ===================================================================

def resilient(
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    timeout_seconds: Optional[float] = None
):
    """Combined decorator with retry, circuit breaker, and timeout"""

    def decorator(func: Callable) -> Callable:
        decorated = func

        # Apply timeout
        if timeout_seconds:
            decorated = timeout(timeout_seconds)(decorated)

        # Apply retry
        if retry_config:
            decorated = retry_async(retry_config)(decorated)

        # Apply circuit breaker
        if circuit_breaker:
            original_func = decorated

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await circuit_breaker.call_async(original_func, *args, **kwargs)

            decorated = wrapper

        return decorated

    return decorator


# ===================================================================
# GLOBAL CIRCUIT BREAKERS
# ===================================================================

# Create circuit breakers for external services
db_circuit_breaker = CircuitBreaker(
    name="database",
    failure_threshold=5,
    timeout=30.0
)

ml_circuit_breaker = CircuitBreaker(
    name="ml-engine",
    failure_threshold=3,
    timeout=60.0
)

external_api_circuit_breaker = CircuitBreaker(
    name="external-api",
    failure_threshold=3,
    timeout=120.0
)


# ===================================================================
# USAGE EXAMPLES
# ===================================================================

"""
# Example 1: Retry with exponential backoff

@retry_async(RetryConfig(
    max_attempts=3,
    strategy=RetryStrategy.EXPONENTIAL,
    retry_on=(ConnectionError, TimeoutError)
))
async def fetch_weather_data(lat: float, lon: float):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/v1/forecast?lat={lat}&lon={lon}"
        )
        return response.json()


# Example 2: Circuit breaker

@circuit_breaker(ml_circuit_breaker)
async def predict_crop_yield(field_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml-engine:8010/api/ml/predict/crop-yield",
            json=field_data,
            timeout=10.0
        )
        return response.json()


# Example 3: Combined resilience

@resilient(
    retry_config=RetryConfig(max_attempts=3),
    circuit_breaker=db_circuit_breaker,
    timeout_seconds=5.0
)
async def save_field_to_database(field: Field):
    async with database.transaction():
        await database.execute(
            "INSERT INTO fields VALUES (...)",
            field.dict()
        )


# Example 4: Monitor circuit breaker

@router.get("/health/circuit-breakers")
async def circuit_breaker_metrics():
    return {
        "database": db_circuit_breaker.get_metrics(),
        "ml_engine": ml_circuit_breaker.get_metrics(),
        "external_api": external_api_circuit_breaker.get_metrics()
    }
"""

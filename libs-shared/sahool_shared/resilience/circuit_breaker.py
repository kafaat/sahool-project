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

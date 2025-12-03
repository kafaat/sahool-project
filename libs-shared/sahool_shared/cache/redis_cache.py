"""
Redis Cache Implementation
تنفيذ التخزين المؤقت Redis
"""

import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union
import os

import redis.asyncio as redis
from redis.asyncio import Redis

T = TypeVar("T")


class RedisCache:
    """
    Redis cache client with async support.
    عميل التخزين المؤقت Redis مع دعم async
    """

    def __init__(
        self,
        url: Optional[str] = None,
        prefix: str = "sahool",
        default_ttl: int = 3600,
    ):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._client is None:
            self._client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> Redis:
        """Get Redis client."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.client.get(self._make_key(key))

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Union[str, dict, list],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        return await self.client.set(self._make_key(key), value, ex=ttl)

    async def delete(self, key: str) -> int:
        """Delete key from cache."""
        return await self.client.delete(self._make_key(key))

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = await self.client.keys(self._make_key(pattern))
        if keys:
            return await self.client.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(self._make_key(key)) > 0

    async def ttl(self, key: str) -> int:
        """Get TTL of key."""
        return await self.client.ttl(self._make_key(key))

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value."""
        return await self.client.incrby(self._make_key(key), amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on key."""
        return await self.client.expire(self._make_key(key), ttl)

    # Rate limiting helpers
    async def rate_limit_check(
        self,
        key: str,
        limit: int,
        window: int = 60,
    ) -> tuple[bool, int]:
        """
        Check rate limit.
        Returns (allowed, current_count).
        """
        import time
        current = int(time.time())
        window_key = f"ratelimit:{key}:{current // window}"

        pipe = self.client.pipeline()
        pipe.incr(self._make_key(window_key))
        pipe.expire(self._make_key(window_key), window + 10)
        results = await pipe.execute()

        count = results[0]
        return count <= limit, count

    # Token blacklist helpers
    async def blacklist_token(self, jti: str, ttl: int) -> bool:
        """Add token to blacklist."""
        return await self.set(f"blacklist:{jti}", "1", ttl)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        return await self.exists(f"blacklist:{jti}")


# Global cache instance
_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.connect()
    return _cache


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    ttl: int = 3600,
    prefix: str = "cache",
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching function results.
    مزخرف لتخزين نتائج الدالة مؤقتاً

    Usage:
        @cached(ttl=300, prefix="weather")
        async def get_weather(lat: float, lon: float):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = await get_cache()

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache.get_json(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)

            # Cache the result
            await cache.set(key, result, ttl)

            return result

        return wrapper
    return decorator

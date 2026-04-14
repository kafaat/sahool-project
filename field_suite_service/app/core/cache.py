"""
Caching Layer for Sahool Yemen
سهول اليمن - طبقة التخزين المؤقت

Redis-based caching with fallback to in-memory cache.
"""
import asyncio
import json
import hashlib
import time
from typing import Any, Optional, TypeVar, Callable
from dataclasses import dataclass, field
from functools import wraps
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheConfig:
    """Cache configuration"""
    default_ttl: int = 300              # 5 minutes
    max_memory_items: int = 1000        # Max items in memory cache
    redis_url: Optional[str] = None
    key_prefix: str = "sahool"
    serialize: bool = True


# =============================================================================
# Cache Interface
# =============================================================================

class CacheInterface(ABC):
    """Abstract cache interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries"""
        pass


# =============================================================================
# In-Memory Cache Implementation
# =============================================================================

@dataclass
class CacheEntry:
    """Single cache entry with expiration"""
    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)
    access_count: int = 0


class InMemoryCache(CacheInterface):
    """
    In-Memory Cache with LRU eviction

    Used as fallback when Redis is unavailable.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.config.key_prefix}:{key}"

    async def _cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if v.expires_at <= now]
        for key in expired:
            del self._cache[key]

    async def _evict_if_needed(self):
        """Evict oldest entries if cache is full"""
        if len(self._cache) >= self.config.max_memory_items:
            # Remove least recently accessed items
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1].access_count
            )
            # Remove 10% of items
            to_remove = max(1, len(sorted_items) // 10)
            for key, _ in sorted_items[:to_remove]:
                del self._cache[key]
                self._stats["evictions"] += 1

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            full_key = self._make_key(key)
            entry = self._cache.get(full_key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.expires_at <= time.time():
                del self._cache[full_key]
                self._stats["misses"] += 1
                return None

            entry.access_count += 1
            self._stats["hits"] += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        async with self._lock:
            await self._cleanup_expired()
            await self._evict_if_needed()

            full_key = self._make_key(key)
            ttl = ttl or self.config.default_ttl
            expires_at = time.time() + ttl

            self._cache[full_key] = CacheEntry(
                value=value,
                expires_at=expires_at
            )
            return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        async with self._lock:
            full_key = self._make_key(key)
            if full_key in self._cache:
                del self._cache[full_key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._lock:
            full_key = self._make_key(key)
            entry = self._cache.get(full_key)
            if entry and entry.expires_at > time.time():
                return True
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            # Pattern matching
            prefix = self._make_key(pattern.replace("*", ""))
            to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in to_delete:
                del self._cache[key]
            return len(to_delete)

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "type": "in_memory",
            "size": len(self._cache),
            "max_size": self.config.max_memory_items,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 4),
            "evictions": self._stats["evictions"],
        }


# =============================================================================
# Redis Cache Implementation
# =============================================================================

class RedisCache(CacheInterface):
    """
    Redis Cache Implementation

    Production-grade caching with Redis backend.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._redis = None
        self._connected = False
        self._fallback = InMemoryCache(config)

    async def connect(self):
        """Connect to Redis"""
        if self.config.redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                self._connected = True
                logger.info("redis_connected", url=self.config.redis_url[:20] + "...")
            except Exception as e:
                logger.warning(
                    "redis_connection_failed",
                    error=str(e),
                    message="Falling back to in-memory cache"
                )
                self._connected = False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._connected = False

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.config.key_prefix}:{key}"

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage"""
        if self.config.serialize:
            return json.dumps(value, default=str)
        return str(value)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage"""
        if self.config.serialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            return await self._fallback.get(key)

        try:
            full_key = self._make_key(key)
            value = await self._redis.get(full_key)
            if value is not None:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.warning("redis_get_error", key=key, error=str(e))
            return await self._fallback.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self._connected:
            return await self._fallback.set(key, value, ttl)

        try:
            full_key = self._make_key(key)
            ttl = ttl or self.config.default_ttl
            serialized = self._serialize(value)
            await self._redis.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning("redis_set_error", key=key, error=str(e))
            return await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self._connected:
            return await self._fallback.delete(key)

        try:
            full_key = self._make_key(key)
            result = await self._redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning("redis_delete_error", key=key, error=str(e))
            return await self._fallback.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            return await self._fallback.exists(key)

        try:
            full_key = self._make_key(key)
            return await self._redis.exists(full_key) > 0
        except Exception as e:
            logger.warning("redis_exists_error", key=key, error=str(e))
            return await self._fallback.exists(key)

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries"""
        if not self._connected:
            return await self._fallback.clear(pattern)

        try:
            search_pattern = self._make_key(pattern or "*")
            keys = []
            async for key in self._redis.scan_iter(search_pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("redis_clear_error", pattern=pattern, error=str(e))
            return await self._fallback.clear(pattern)

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self._connected:
            stats = self._fallback.get_stats()
            stats["type"] = "in_memory_fallback"
            return stats

        try:
            info = await self._redis.info("stats")
            memory = await self._redis.info("memory")

            return {
                "type": "redis",
                "connected": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used": memory.get("used_memory_human", "unknown"),
                "total_keys": await self._redis.dbsize(),
            }
        except Exception:
            return {"type": "redis", "connected": False}


# =============================================================================
# Cache Manager
# =============================================================================

class CacheManager:
    """
    Cache Manager for the application

    Provides unified caching interface with multiple backends.
    """

    _instance: Optional['CacheManager'] = None

    def __new__(cls, config: Optional[CacheConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[CacheConfig] = None):
        if self._initialized:
            return

        self.config = config or CacheConfig()
        self._cache: CacheInterface = InMemoryCache(self.config)
        self._initialized = True

    async def initialize(self, redis_url: Optional[str] = None):
        """Initialize cache with Redis if available"""
        if redis_url:
            self.config.redis_url = redis_url
            redis_cache = RedisCache(self.config)
            await redis_cache.connect()
            if redis_cache._connected:
                self._cache = redis_cache
                logger.info("cache_initialized", backend="redis")
            else:
                logger.info("cache_initialized", backend="in_memory")
        else:
            logger.info("cache_initialized", backend="in_memory")

    async def shutdown(self):
        """Shutdown cache connections"""
        if isinstance(self._cache, RedisCache):
            await self._cache.disconnect()

    async def get(self, key: str) -> Optional[Any]:
        return await self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        return await self._cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        return await self._cache.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._cache.exists(key)

    async def clear(self, pattern: Optional[str] = None) -> int:
        return await self._cache.clear(pattern)

    def get_stats(self) -> dict:
        if hasattr(self._cache, 'get_stats'):
            if asyncio.iscoroutinefunction(self._cache.get_stats):
                return {"type": "async", "note": "call get_stats_async()"}
            return self._cache.get_stats()
        return {}

    async def get_stats_async(self) -> dict:
        if isinstance(self._cache, RedisCache):
            return await self._cache.get_stats()
        return self._cache.get_stats()


# Global cache instance
cache_manager = CacheManager()


# =============================================================================
# Caching Decorators
# =============================================================================

def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator to cache function results

    Usage:
        @cached(ttl=60, key_prefix="weather")
        async def get_weather(field_id: int):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        prefix = key_prefix or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = generate_cache_key(*args, **kwargs)

            cache_key = f"{prefix}:{key_suffix}"

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", key=cache_key)
                return cached_value

            # Execute function and cache result
            logger.debug("cache_miss", key=cache_key)
            result = await func(*args, **kwargs)

            if result is not None:
                await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache after function execution

    Usage:
        @invalidate_cache("weather:*")
        async def update_weather(field_id: int, data: dict):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            result = await func(*args, **kwargs)
            await cache_manager.clear(pattern)
            logger.debug("cache_invalidated", pattern=pattern)
            return result
        return wrapper
    return decorator


# =============================================================================
# Specialized Caches
# =============================================================================

class YemenRegionCache:
    """
    Specialized cache for Yemen region data

    Caches region, crop, and geographic data with longer TTLs.
    """

    def __init__(self, cache: CacheManager):
        self._cache = cache

    async def get_regions(self) -> Optional[list]:
        return await self._cache.get("yemen:regions")

    async def set_regions(self, regions: list):
        # Region data rarely changes - cache for 24 hours
        await self._cache.set("yemen:regions", regions, ttl=86400)

    async def get_crops(self) -> Optional[list]:
        return await self._cache.get("yemen:crops")

    async def set_crops(self, crops: list):
        await self._cache.set("yemen:crops", crops, ttl=86400)

    async def get_weather(self, region_id: int) -> Optional[dict]:
        return await self._cache.get(f"yemen:weather:{region_id}")

    async def set_weather(self, region_id: int, weather: dict):
        # Weather updates every 30 minutes
        await self._cache.set(f"yemen:weather:{region_id}", weather, ttl=1800)

    async def get_ndvi(self, field_id: int) -> Optional[dict]:
        return await self._cache.get(f"yemen:ndvi:{field_id}")

    async def set_ndvi(self, field_id: int, ndvi: dict):
        # NDVI updates daily
        await self._cache.set(f"yemen:ndvi:{field_id}", ndvi, ttl=86400)


# Specialized cache instance
region_cache = YemenRegionCache(cache_manager)

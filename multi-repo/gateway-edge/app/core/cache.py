import json, asyncio
from typing import Any, Optional
import redis.asyncio as redis
from .config import settings
_redis: Optional[redis.Redis]=None
_lock=asyncio.Lock()
async def redis_client():
    global _redis
    if _redis: return _redis
    async with _lock:
        if _redis is None:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return _redis
async def cache_get(key: str):
    r=await redis_client(); val=await r.get(key)
    return json.loads(val) if val else None
async def cache_set(key: str, value: Any, ttl: int):
    r=await redis_client(); await r.set(key, json.dumps(value), ex=ttl)
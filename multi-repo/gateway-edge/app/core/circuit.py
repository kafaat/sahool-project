import time
from functools import wraps
from typing import Callable, Dict, Tuple
from fastapi import HTTPException
from .config import settings
_state: Dict[Tuple[str,str], dict] = {}
def circuit_guard(method: str):
    def deco(fn: Callable):
        @wraps(fn)
        async def wrapper(url: str, *args, **kwargs):
            key = (method, url.split("/")[2] if "://" in url else url)
            s = _state.get(key, {"failures":0, "opened_at":0})
            if s["failures"] >= settings.CIRCUIT_FAILURES:
                if time.time() - s["opened_at"] < settings.CIRCUIT_RESET_SECONDS:
                    raise HTTPException(503, "downstream_unavailable")
                s = {"failures":0, "opened_at":0}
            try:
                res = await fn(url, *args, **kwargs)
                s["failures"] = 0; _state[key]=s
                return res
            except Exception:
                s["failures"] += 1
                if s["failures"] >= settings.CIRCUIT_FAILURES:
                    s["opened_at"] = time.time()
                _state[key]=s
                raise
        return wrapper
    return deco
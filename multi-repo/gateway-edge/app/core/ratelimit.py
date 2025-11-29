import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from .config import settings
_hits=defaultdict(deque)
def rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now=time.time(); q=_hits[ip]
    while q and now-q[0]>1: q.popleft()
    if len(q)>=settings.RATE_LIMIT_RPS: raise HTTPException(429,"rate_limited")
    q.append(now)
import httpx
from typing import Any, Dict, Optional
async def get_json(url: str, params: Optional[Dict[str,Any]]=None):
    async with httpx.AsyncClient(timeout=20) as c:
        r=await c.get(url, params=params); r.raise_for_status(); return r.json()
import httpx
from typing import Any, Dict, Optional
from .circuit import circuit_guard
@circuit_guard("GET")
async def get_json(url: str, params: Optional[Dict[str,Any]]=None, headers: Optional[Dict[str,str]]=None):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(url, params=params, headers=headers); r.raise_for_status(); return r.json()
@circuit_guard("POST")
async def post_json(url: str, json_body: Dict[str,Any], params: Optional[Dict[str,Any]]=None, headers: Optional[Dict[str,str]]=None):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=json_body, params=params, headers=headers); r.raise_for_status(); return r.json()
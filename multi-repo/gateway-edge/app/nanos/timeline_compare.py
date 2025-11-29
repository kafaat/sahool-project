from ..core.config import settings
from ..core.http_client import get_json
from ..core.cache import cache_get, cache_set
async def build_timeline_compare(field_id: str, tenant_id: str, from_date: str, to_date: str):
    key=f"nano:timeline:{tenant_id}:{field_id}:{from_date}:{to_date}"
    cached=await cache_get(key)
    if cached: return cached
    timeline=await get_json(f"{settings.IMAGERY_CORE_URL}/fields/{field_id}/indices/timeline",
                            params={"tenant_id":tenant_id,"from_date":from_date,"to_date":to_date})
    out={"field_id":field_id,"from":from_date,"to":to_date,"before":timeline[0] if timeline else None,
         "after":timeline[-1] if timeline else None,"timeline":timeline}
    await cache_set(key,out,settings.CACHE_TTL_SECONDS); return out
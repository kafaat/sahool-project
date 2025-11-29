from ..core.config import settings
from ..core.http_client import get_json
from ..core.cache import cache_get, cache_set
async def build_field_overview(field_id: str, tenant_id: str):
    key=f"nano:overview:{tenant_id}:{field_id}"
    cached=await cache_get(key)
    if cached: return cached
    fields=await get_json(f"{settings.GEO_CORE_URL}/v1/fields", params={"tenant_id":tenant_id})
    field=next((f for f in fields if f.get("id")==field_id), None)
    latest=await get_json(f"{settings.IMAGERY_CORE_URL}/fields/{field_id}/indices/latest", params={"tenant_id":tenant_id})
    weather=await get_json(f"{settings.WEATHER_CORE_URL}/v1/weather/current", params={"tenant_id":tenant_id,"field_id":field_id})
    alerts=[]
    try:
        alerts=await get_json(f"{settings.ALERTS_CORE_URL}/v1/alerts/recent", params={"tenant_id":tenant_id,"hours":72})
    except Exception: pass
    out={"field":field,"latest_indices":latest,"weather_current":weather,"recent_alerts":alerts[:10]}
    await cache_set(key,out,settings.CACHE_TTL_SECONDS); return out
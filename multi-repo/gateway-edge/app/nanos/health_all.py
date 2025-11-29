from ..core.config import settings
from ..core.http_client import get_json
async def health_all():
    svcs={"geo":f"{settings.GEO_CORE_URL}/health","imagery":f"{settings.IMAGERY_CORE_URL}/health",
          "soil":f"{settings.SOIL_CORE_URL}/health","weather":f"{settings.WEATHER_CORE_URL}/health",
          "alerts":f"{settings.ALERTS_CORE_URL}/health","analytics":f"{settings.ANALYTICS_CORE_URL}/health"}
    out={}
    for k,u in svcs.items():
        try: out[k]=await get_json(u)
        except Exception as e: out[k]={"status":"down","error":str(e)}
    return out
from .registry import tool
from ..core.config import settings
from ..core.http_client import get_json
@tool("field_overview")
async def field_overview(tenant_id:str, field_id:str):
    return await get_json(f"{settings.GATEWAY_URL}/v1/nano/fields/{field_id}/overview", params={"tenant_id":tenant_id})
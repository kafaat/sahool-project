from typing import Dict, Any
from .tools.registry import TOOLS
async def generate_reply(req: Dict[str,Any]) -> Dict[str,Any]:
    tenant_id=req["tenant_id"]; field_id=req.get("field_id")
    if not field_id:
        return {"reply":"أخبرني رقم الحقل لأعطيك تحليلًا دقيقًا."}
    ov=await TOOLS["field_overview"](tenant_id=tenant_id, field_id=field_id)
    latest=ov.get("latest_indices",{}) or {}
    ndvi=latest.get("ndvi_mean")
    recs=[]
    if ndvi is not None and ndvi<0.35:
        recs.append({"type":"scouting","priority":"high","title":"فحص ميداني عاجل","reason":"NDVI منخفض."})
    reply="إليك ملخص الحقل." + ("\n- "+"\n- ".join([r["title"] for r in recs]) if recs else " الوضع طبيعي.")
    return {"reply":reply,"actions":recs,"debug":{"used_tools":["field_overview"]}}
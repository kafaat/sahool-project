from typing import Dict, Any, List

from app.core.config import get_settings
from app.core.http_client import get_json

settings = get_settings()

async def get_field_context(tenant_id: int, field_id: int) -> Dict[str, Any]:
    base = settings.GATEWAY_URL

    # NOTE: using gateway-edge proxy to reach services
    imagery = await get_json(f"{base}/api/imagery/api/v1/imagery/list",
                             params={"tenant_id": tenant_id, "field_id": field_id})
    soil_summary = await get_json(f"{base}/api/soil/api/v1/soil/fields/{field_id}/summary",
                                  params={"tenant_id": tenant_id})
    weather_forecast = await get_json(f"{base}/api/weather/api/v1/weather/forecast",
                                      params={"tenant_id": tenant_id, "field_id": field_id, "hours_ahead": 72})
    alerts = await get_json(f"{base}/api/alerts/api/v1/alerts/recent",
                            params={"tenant_id": tenant_id, "hours": 72})

    # take latest image if exists
    latest_image = imagery[0] if imagery else None

    context = {
        "imagery_latest": latest_image,
        "soil_summary": soil_summary,
        "weather_forecast": weather_forecast,
        "alerts": alerts,
    }
    return context


def _safe_get(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def basic_reasoning(context: Dict[str, Any]) -> Dict[str, Any]:
    recommendations: List[str] = []
    warnings: List[str] = []

    soil_summary = context.get("soil_summary") or {}
    weather = context.get("weather_forecast") or {}
    alerts = context.get("alerts") or []

    # Simple rule examples
    ec = soil_summary.get("ec_avg")
    ph = soil_summary.get("ph_avg")
    moisture = soil_summary.get("moisture_avg")

    if ec is not None and ec > 4:
        warnings.append("ملوحة التربة مرتفعة، يوصى بالتفكير في غسيل التربة وتحسين الصرف.")
    if ph is not None and (ph < 6 or ph > 7.5):
        warnings.append("درجة حموضة التربة خارج النطاق المثالي، راجع برنامج التسميد/الجبس الزراعي.")
    if moisture is not None and moisture < 15:
        warnings.append("رطوبة التربة منخفضة، يوصى بالري خلال 24 ساعة القادمة.")

    points = weather.get("points") or []
    if points:
        max_eto = max((p.get("eto_mm") or 0) for p in points)
        if max_eto > 7:
            warnings.append("قيمة ETo المتوقعة عالية، قد يحدث إجهاد مائي للمحصول.")

    if not warnings:
        recommendations.append("الظروف الحالية تبدو مستقرة، استمر ببرنامج الري والتسميد المعتاد مع متابعة المؤشرات.")

    # Simple prioritization
    priority = "normal"
    if any("إجهاد" in w or "مرتفعة" in w for w in warnings):
        priority = "high"

    return {
        "priority": priority,
        "warnings": warnings,
        "recommendations": recommendations,
    }


async def build_field_advice(tenant_id: int, field_id: int, message: str) -> Dict[str, Any]:
    context = await get_field_context(tenant_id, field_id)
    analysis = basic_reasoning(context)

    reply_lines = []
    if analysis["priority"] == "high":
        reply_lines.append("⚠️ توجد بعض المؤشرات التي تحتاج انتباهك في هذا الحقل:")
    else:
        reply_lines.append("✅ لا توجد مؤشرات خطيرة حالياً، لكن هذه ملاحظات مفيدة:")

    for w in analysis["warnings"]:
        reply_lines.append(f"- {w}")
    for r in analysis["recommendations"]:
        reply_lines.append(f"- {r}")

    reply = "\n".join(reply_lines)

    return {
        "reply": reply,
        "priority": analysis["priority"],
        "context": {
            "soil_summary": context.get("soil_summary"),
            "weather_forecast": context.get("weather_forecast"),
        },
    }
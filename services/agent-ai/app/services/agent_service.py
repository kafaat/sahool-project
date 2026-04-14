from typing import Any, Dict, List

import httpx

from app.core.config import get_settings
from app.services.ndvi_analyzer import analyze_ndvi_image
from app.services.alert_bridge import send_ndvi_alerts

settings = get_settings()


async def get_field_context(tenant_id: int, field_id: int) -> Dict[str, Any]:
    """Collect basic soil + weather + alerts context via gateway-edge."""
    base = settings.GATEWAY_URL + "/api"

    async with httpx.AsyncClient(timeout=30) as client:
        imagery_resp = await client.get(
            f"{base}/imagery/api/v1/imagery/list",
            params={"tenant_id": tenant_id, "field_id": field_id},
        )
        soil_resp = await client.get(
            f"{base}/soil/api/v1/soil/fields/{field_id}/summary",
            params={"tenant_id": tenant_id},
        )
        weather_resp = await client.get(
            f"{base}/weather/api/v1/weather/forecast",
            params={"tenant_id": tenant_id, "field_id": field_id, "hours_ahead": 72},
        )
        alerts_resp = await client.get(
            f"{base}/alerts/api/v1/alerts/recent",
            params={"tenant_id": tenant_id, "hours": 72},
        )

    imagery = imagery_resp.json()
    soil_summary = soil_resp.json()
    weather_forecast = weather_resp.json()
    alerts = alerts_resp.json()

    latest_image = imagery[0] if isinstance(imagery, list) and imagery else None

    return {
        "imagery_latest": latest_image,
        "soil_summary": soil_summary,
        "weather_forecast": weather_forecast,
        "alerts": alerts,
    }


def basic_reasoning(context: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[str] = []
    recommendations: List[str] = []

    soil_summary = context.get("soil_summary") or {}
    weather = context.get("weather_forecast") or {}

    ec = soil_summary.get("ec_avg")
    ph = soil_summary.get("ph_avg")
    moisture = soil_summary.get("moisture_avg")

    if ec is not None and ec > 4:
        warnings.append(
            "ملوحة التربة مرتفعة، يوصى بالتفكير في غسيل التربة وتحسين الصرف."
        )
    if ph is not None and (ph < 6 or ph > 7.5):
        warnings.append(
            "درجة حموضة التربة خارج النطاق المثالي، راجع برنامج التسميد/الجبس الزراعي."
        )
    if moisture is not None and moisture < 15:
        warnings.append("رطوبة التربة منخفضة، يوصى بالري خلال 24 ساعة القادمة.")

    points = (weather or {}).get("points") or []
    if points:
        max_eto = max((p.get("eto_mm") or 0) for p in points)
        if max_eto > 7:
            warnings.append(
                "قيمة ETo المتوقعة عالية، قد يحدث إجهاد مائي للمحصول خلال الأيام القادمة."
            )

    if not warnings:
        recommendations.append(
            "الظروف الحالية تبدو مستقرة، استمر ببرنامج الري والتسميد المعتاد مع متابعة المؤشرات."
        )

    priority = "normal"
    if any("إجهاد" in w or "مرتفعة" in w for w in warnings):
        priority = "high"

    return {"priority": priority, "warnings": warnings, "recommendations": recommendations}


async def build_field_advice(tenant_id: int, field_id: int, message: str) -> Dict[str, Any]:
    context = await get_field_context(tenant_id, field_id)
    analysis = basic_reasoning(context)

    reply_lines: List[str] = []
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


async def get_ndvi_analysis(tenant_id: int, field_id: int) -> Dict[str, Any]:
    """Fetch latest NDVI via gateway-edge and analyze color-based stress, then send alerts if needed."""
    base = settings.GATEWAY_URL + "/api"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{base}/imagery/api/v1/imagery/fields/{field_id}/ndvi-latest",
            params={"tenant_id": tenant_id},
        )

    if resp.status_code != 200:
        return {
            "ndvi_available": False,
            "message": "لا توجد بيانات NDVI متاحة لهذا الحقل حالياً.",
        }

    data = resp.json()
    ndvi_url = data.get("ndvi_preview_png") or data.get("ndvi_path")
    if not ndvi_url:
        return {
            "ndvi_available": False,
            "message": "لا توجد صورة NDVI جاهزة للعرض.",
        }

    stats = analyze_ndvi_image(ndvi_url)

    severe = float(stats.get("severe", 0.0))
    stress = float(stats.get("stress", 0.0))
    excellent = float(stats.get("excellent", 0.0))
    good = float(stats.get("good", 0.0))

    recommendations: List[str] = []

    if severe > 0.15:
        recommendations.append(
            f"⚠️ حوالي {severe*100:.1f}% من مساحة الحقل في حالة إجهاد شديد، يوصى بفحص تلك المناطق ميدانياً."
        )
    if stress > 0.20:
        recommendations.append(
            f"🔶 حوالي {stress*100:.1f}% من مساحة الحقل تعاني من إجهاد متوسط، راجع برنامج الري والتسميد."
        )
    if excellent > 0.30:
        recommendations.append(
            f"🌿 أكثر من {excellent*100:.1f}% من الحقل في حالة نمو ممتاز."
        )
    if good > 0.30 and excellent < 0.3:
        recommendations.append(
            f"✅ الحقل في حالة جيدة إجمالاً، لكن توجد مناطق يمكن تحسينها."
        )

    if not recommendations:
        recommendations.append(
            "🌱 توزيع NDVI متوازن ولا توجد مؤشرات قوية على إجهاد واسع النطاق."
        )

    priority = "normal"
    if severe > 0.15 or stress > 0.35:
        priority = "high"

    # 🔴 إرسال تنبيهات فعلية إلى alerts-core عند الحالات الحرجة
    await send_ndvi_alerts(tenant_id, field_id, stats, priority)

    return {
        "ndvi_available": True,
        "ndvi_url": ndvi_url,
        "stats": stats,
        "priority": priority,
        "recommendations": recommendations,
    }

from typing import Any, Dict, List

import httpx

from app.core.config import get_settings
from app.services.ndvi_analyzer import analyze_ndvi_image
from app.services.alert_bridge import send_ndvi_alerts

settings = get_settings()


async def get_field_context(tenant_id: str, field_id: str) -> Dict[str, Any]:
    """Collect basic soil + weather + alerts context via gateway."""
    base = settings.GATEWAY_URL
    headers = {"X-Tenant-ID": str(tenant_id)}

    async with httpx.AsyncClient(timeout=30) as client:
        imagery_resp = await client.get(
            f"{base}/api/v1/imagery/list",
            params={"field_id": field_id},
            headers=headers,
        )
        weather_resp = await client.get(
            f"{base}/api/v1/weather/fields/{field_id}",
            headers=headers,
        )
        alerts_resp = await client.get(
            f"{base}/api/v1/alerts/field/{field_id}",
            headers=headers,
        )
        analytics_resp = await client.get(
            f"{base}/api/v1/analytics/fields/{field_id}/summary",
            headers=headers,
        )

    imagery = imagery_resp.json() if imagery_resp.status_code == 200 else {}
    weather_forecast = weather_resp.json() if weather_resp.status_code == 200 else {}
    alerts = alerts_resp.json() if alerts_resp.status_code == 200 else {}
    analytics = analytics_resp.json() if analytics_resp.status_code == 200 else {}

    latest_image = imagery[0] if isinstance(imagery, list) and imagery else None

    return {
        "imagery_latest": latest_image,
        "analytics_summary": analytics,
        "weather_forecast": weather_forecast,
        "alerts": alerts,
    }


def basic_reasoning(context: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[str] = []
    recommendations: List[str] = []

    analytics = context.get("analytics_summary") or {}
    weather = context.get("weather_forecast") or {}
    alerts = context.get("alerts") or {}

    # Check NDVI-based health
    ndvi = analytics.get("latest_ndvi")
    health_status = analytics.get("health_status", "").lower()

    if ndvi is not None and ndvi < 0.3:
        warnings.append(
            "مؤشر NDVI منخفض، يوصى بفحص صحة المحصول والتسميد."
        )
    if "poor" in health_status or "stress" in health_status:
        warnings.append(
            "حالة المحصول تحتاج اهتمام، راجع برنامج الري والتسميد."
        )

    # Check weather conditions
    current = weather.get("current") or {}
    temperature = current.get("temperature")
    humidity = current.get("humidity")

    if temperature is not None and temperature > 38:
        warnings.append(
            "درجة الحرارة مرتفعة جداً، قد يحدث إجهاد حراري للمحصول."
        )
    if humidity is not None and humidity < 20:
        warnings.append(
            "الرطوبة منخفضة جداً، يوصى بزيادة الري."
        )

    # Check alerts
    alert_items = alerts.get("items") or []
    if len(alert_items) > 0:
        high_alerts = [a for a in alert_items if a.get("severity") == "high"]
        if high_alerts:
            warnings.append(
                f"يوجد {len(high_alerts)} تنبيه عاجل للحقل، راجع قائمة التنبيهات."
            )

    if not warnings:
        recommendations.append(
            "الظروف الحالية تبدو مستقرة، استمر ببرنامج الري والتسميد المعتاد مع متابعة المؤشرات."
        )

    priority = "normal"
    if any("إجهاد" in w or "مرتفعة" in w or "عاجل" in w for w in warnings):
        priority = "high"

    return {"priority": priority, "warnings": warnings, "recommendations": recommendations}


async def build_field_advice(tenant_id: str, field_id: str, message: str) -> Dict[str, Any]:
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
            "analytics_summary": context.get("analytics_summary"),
            "weather_forecast": context.get("weather_forecast"),
        },
    }


async def get_ndvi_analysis(tenant_id: str, field_id: str) -> Dict[str, Any]:
    """Fetch latest NDVI via gateway and analyze color-based stress, then send alerts if needed."""
    base = settings.GATEWAY_URL
    headers = {"X-Tenant-ID": str(tenant_id)}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{base}/api/v1/ndvi/fields/{field_id}",
            headers=headers,
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

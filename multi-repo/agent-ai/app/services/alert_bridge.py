import httpx
from typing import Dict

from app.core.config import get_settings

settings = get_settings()


async def send_ndvi_alerts(tenant_id: int, field_id: int, stats: Dict[str, float], priority: str) -> None:
    """يرسل تنبيهات إلى alerts-core بناءً على حالة NDVI الحرجة.
    - إذا priority = high أو severe > 0.15 → تنبيه عالي.
    - إذا stress > 0.20 → تنبيه متوسط.
    """
    base = settings.GATEWAY_URL + "/api"
    severe = float(stats.get("severe", 0.0))
    stress = float(stats.get("stress", 0.0))

    async with httpx.AsyncClient(timeout=30) as client:
        # severe alert
        if severe > 0.15 or priority == "high":
            await client.post(
                f"{base}/alerts/api/v1/alerts",
                json={
                    "tenant_id": tenant_id,
                    "field_id": field_id,
                    "category": "ndvi",
                    "severity": "high",
                    "title": "إجهاد نباتي شديد (NDVI)",
                    "message": f"حوالي {severe*100:.1f}% من مساحة الحقل في حالة إجهاد شديد وفقاً لخريطة NDVI.",
                },
            )

        # medium stress alert
        if stress > 0.20:
            await client.post(
                f"{base}/alerts/api/v1/alerts",
                json={
                    "tenant_id": tenant_id,
                    "field_id": field_id,
                    "category": "ndvi",
                    "severity": "medium",
                    "title": "مناطق إجهاد متوسطة (NDVI)",
                    "message": f"حوالي {stress*100:.1f}% من مساحة الحقل تعاني من إجهاد متوسط.",
                },
            )

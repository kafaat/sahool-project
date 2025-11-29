
from app.schemas.analytics import FieldHealth, FieldStress, Insights
from app.core.config import get_settings

settings = get_settings()
def compute_health(ndvi: float, ph: float, ec: float, eto: float) -> FieldHealth:
    """Compute a composite health index for a field.

    This function intentionally keeps the model simple and transparent, but all
    thresholds can be tuned via settings in the future.
    """
    # Clamp NDVI between -1 and 1
    ndvi = max(-1.0, min(1.0, ndvi))
    # Map NDVI -> [0,1]
    ndvi_score = max(0.0, min(1.0, (ndvi + 1.0) / 2.0))

    # Soil pH: ideal around neutral 7.0, degrade smoothly as it moves away
    ph_ideal = getattr(settings, "PH_IDEAL", 7.0)
    ph_span = getattr(settings, "PH_SPAN", 7.5)
    soil_score = max(0.0, min(1.0, (ph_span - abs(ph - ph_ideal)) / ph_span))

    # Weather/ETo: higher ETo usually implies more water demand; keep it simple
    eto_max = getattr(settings, "ETO_MAX", 10.0)
    weather_score = max(0.0, min(1.0, 1.0 - (eto / eto_max)))

    total = (ndvi_score + soil_score + weather_score) / 3.0
    return FieldHealth(
        ndvi_score=ndvi_score,
        soil_score=soil_score,
        weather_score=weather_score,
        total_health=total,
    )

def compute_stress(ec: float, eto: float, temp: float) -> FieldStress:
    water = min(1, eto / 10)
    heat = min(1, max(0, (temp - 35) / 15))
    salinity = min(1, ec / 8)
    combined = (water + heat + salinity) / 3
    return FieldStress(
        water_stress=water,
        heat_stress=heat,
        salinity_stress=salinity,
        combined_stress=combined
    )

def generate_insights(health: FieldHealth, stress: FieldStress) -> Insights:
    rec = []
    if stress.water_stress > 0.6:
        rec.append("زيادة الري وتقليل الفاقد")
    if stress.salinity_stress > 0.6:
        rec.append("إجراء غسيل للتربة وتقليل الأملاح")
    if health.ndvi_score < 0.4:
        rec.append("فحص الحقل ميدانياً لضعف النمو")
    if not rec:
        rec.append("الحالة جيدة — لا يوجد توصيات حرجة")
    return Insights(recommendations=rec)

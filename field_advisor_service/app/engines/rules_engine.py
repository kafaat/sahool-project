"""
Rules Engine for Field Advisor
Implements rule-based recommendation and alert generation
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from ..core.config import settings
from ..core.logging import logger
from ..schemas.advisor import (
    FieldContext,
    RecommendationResponse,
    AlertResponse,
    RecommendationType,
    AlertSeverity,
    AlertStatus,
    NDVITrend,
    RiskLevel,
)


class RulesEngine:
    """
    Rule-based engine for generating recommendations and alerts
    """

    def __init__(self):
        # Thresholds
        self.ndvi_critical = settings.ndvi_critical_threshold  # 0.3
        self.ndvi_warning = settings.ndvi_warning_threshold    # 0.4
        self.ndvi_healthy = settings.ndvi_healthy_threshold    # 0.6

        # Weather thresholds
        self.temp_high = 40.0  # Celsius
        self.temp_low = 5.0
        self.humidity_low = 30.0
        self.humidity_high = 85.0
        self.wind_high = 50.0  # km/h

    def analyze(
        self,
        context: FieldContext,
        language: str = "en",
    ) -> Tuple[List[RecommendationResponse], List[AlertResponse], float, RiskLevel]:
        """
        Analyze field context and generate recommendations/alerts

        Returns:
            Tuple of (recommendations, alerts, health_score, risk_level)
        """
        logger.info(f"Running rules engine for field {context.field_id}")

        recommendations: List[RecommendationResponse] = []
        alerts: List[AlertResponse] = []

        # Calculate health score (0-100)
        health_score = self._calculate_health_score(context)

        # Run NDVI rules
        ndvi_recs, ndvi_alerts = self._run_ndvi_rules(context, language)
        recommendations.extend(ndvi_recs)
        alerts.extend(ndvi_alerts)

        # Run weather rules
        weather_recs, weather_alerts = self._run_weather_rules(context, language)
        recommendations.extend(weather_recs)
        alerts.extend(weather_alerts)

        # Run irrigation rules
        irrigation_recs = self._run_irrigation_rules(context, language)
        recommendations.extend(irrigation_recs)

        # Run fertilization rules
        fert_recs = self._run_fertilization_rules(context, language)
        recommendations.extend(fert_recs)

        # Run growth stage rules
        growth_recs = self._run_growth_stage_rules(context, language)
        recommendations.extend(growth_recs)

        # Calculate risk level
        risk_level = self._calculate_risk_level(health_score, alerts)

        # Sort recommendations by priority
        recommendations.sort(key=lambda x: x.priority, reverse=True)

        logger.info(
            f"Generated {len(recommendations)} recommendations and {len(alerts)} alerts"
        )

        return recommendations, alerts, health_score, risk_level

    def _calculate_health_score(self, context: FieldContext) -> float:
        """Calculate overall field health score (0-100)"""
        score = 70.0  # Base score

        if context.ndvi:
            # NDVI contribution (40% weight)
            ndvi_score = context.ndvi.mean * 100
            if context.ndvi.mean < self.ndvi_critical:
                ndvi_score = context.ndvi.mean * 60  # Penalize heavily
            elif context.ndvi.mean < self.ndvi_warning:
                ndvi_score = context.ndvi.mean * 80  # Penalize moderately

            # Trend adjustment
            if context.ndvi.trend == NDVITrend.DECLINING:
                ndvi_score *= 0.9
            elif context.ndvi.trend == NDVITrend.IMPROVING:
                ndvi_score *= 1.05

            score = score * 0.6 + ndvi_score * 0.4

        if context.weather:
            # Weather impact (20% weight)
            weather_penalty = 0

            if context.weather.temperature_current:
                if context.weather.temperature_current > self.temp_high:
                    weather_penalty += 10
                elif context.weather.temperature_current < self.temp_low:
                    weather_penalty += 15

            if context.weather.humidity:
                if context.weather.humidity < self.humidity_low:
                    weather_penalty += 5
                elif context.weather.humidity > self.humidity_high:
                    weather_penalty += 3

            score -= weather_penalty * 0.2

        if context.soil:
            # Soil health contribution (15% weight)
            soil_score = 70

            if context.soil.ph:
                # Optimal pH range: 6.0-7.5
                if 6.0 <= context.soil.ph <= 7.5:
                    soil_score += 10
                else:
                    soil_score -= 10

            if context.soil.moisture:
                # Optimal moisture: 30-60%
                if 30 <= context.soil.moisture <= 60:
                    soil_score += 10
                elif context.soil.moisture < 20:
                    soil_score -= 15

            score = score * 0.85 + soil_score * 0.15

        return max(0, min(100, score))

    def _calculate_risk_level(
        self,
        health_score: float,
        alerts: List[AlertResponse],
    ) -> RiskLevel:
        """Calculate overall risk level"""
        critical_count = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
        warning_count = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)

        if critical_count > 0 or health_score < 30:
            return RiskLevel.CRITICAL
        elif warning_count > 2 or health_score < 50:
            return RiskLevel.HIGH
        elif warning_count > 0 or health_score < 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _run_ndvi_rules(
        self,
        context: FieldContext,
        language: str,
    ) -> Tuple[List[RecommendationResponse], List[AlertResponse]]:
        """Run NDVI-based rules"""
        recommendations = []
        alerts = []

        if not context.ndvi:
            return recommendations, alerts

        ndvi = context.ndvi

        # Rule: Critical NDVI
        if ndvi.mean < self.ndvi_critical:
            alerts.append(AlertResponse(
                id=uuid4(),
                severity=AlertSeverity.CRITICAL,
                status=AlertStatus.ACTIVE,
                title="Critical Vegetation Health",
                title_ar="صحة نباتية حرجة",
                message=f"NDVI is critically low at {ndvi.mean:.2f}. Immediate investigation required.",
                message_ar=f"مؤشر NDVI منخفض بشكل حرج عند {ndvi.mean:.2f}. يلزم التحقيق الفوري.",
                alert_type="ndvi_critical",
                threshold_value=self.ndvi_critical,
                actual_value=ndvi.mean,
                created_at=datetime.utcnow(),
            ))

            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.GENERAL,
                title="Urgent Field Inspection Required",
                title_ar="مطلوب فحص عاجل للحقل",
                description="Conduct immediate field inspection to identify cause of low vegetation health. Check for pest damage, disease, water stress, or nutrient deficiency.",
                description_ar="قم بفحص ميداني فوري لتحديد سبب انخفاض صحة النباتات. تحقق من أضرار الآفات أو الأمراض أو إجهاد المياه أو نقص المغذيات.",
                priority=10,
                urgency="immediate",
                confidence_score=0.95,
                rule_source="ndvi_critical_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: Warning NDVI
        elif ndvi.mean < self.ndvi_warning:
            alerts.append(AlertResponse(
                id=uuid4(),
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Low Vegetation Health",
                title_ar="صحة نباتية منخفضة",
                message=f"NDVI is below optimal at {ndvi.mean:.2f}. Consider investigating.",
                message_ar=f"مؤشر NDVI أقل من المستوى الأمثل عند {ndvi.mean:.2f}. يُنصح بالتحقيق.",
                alert_type="ndvi_warning",
                threshold_value=self.ndvi_warning,
                actual_value=ndvi.mean,
                created_at=datetime.utcnow(),
            ))

        # Rule: Declining trend
        if ndvi.trend == NDVITrend.DECLINING:
            alerts.append(AlertResponse(
                id=uuid4(),
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Declining Vegetation Trend",
                title_ar="اتجاه تراجعي في الغطاء النباتي",
                message="NDVI has been declining over recent measurements. Monitor closely.",
                message_ar="مؤشر NDVI في تراجع خلال القياسات الأخيرة. يُنصح بالمراقبة الدقيقة.",
                alert_type="ndvi_declining",
                created_at=datetime.utcnow(),
            ))

        # Rule: Zone variability
        if ndvi.zones:
            low_zones = [z for z in ndvi.zones if z.get("zone") == "low"]
            if low_zones and low_zones[0].get("percentage", 0) > 20:
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.GENERAL,
                    title="Address Low-NDVI Zones",
                    title_ar="معالجة المناطق ذات NDVI المنخفض",
                    description=f"About {low_zones[0].get('percentage')}% of the field shows low vegetation health. Consider targeted intervention in these areas.",
                    description_ar=f"حوالي {low_zones[0].get('percentage')}% من الحقل يظهر صحة نباتية منخفضة. يُنصح بالتدخل المستهدف في هذه المناطق.",
                    priority=7,
                    urgency="normal",
                    affected_zones=["low"],
                    confidence_score=0.85,
                    rule_source="zone_variability_rule",
                    created_at=datetime.utcnow(),
                ))

        return recommendations, alerts

    def _run_weather_rules(
        self,
        context: FieldContext,
        language: str,
    ) -> Tuple[List[RecommendationResponse], List[AlertResponse]]:
        """Run weather-based rules"""
        recommendations = []
        alerts = []

        if not context.weather:
            return recommendations, alerts

        weather = context.weather

        # Rule: High temperature
        if weather.temperature_current and weather.temperature_current > self.temp_high:
            alerts.append(AlertResponse(
                id=uuid4(),
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="High Temperature Alert",
                title_ar="تنبيه درجة حرارة مرتفعة",
                message=f"Current temperature is {weather.temperature_current}°C. Consider heat stress mitigation.",
                message_ar=f"درجة الحرارة الحالية {weather.temperature_current}°م. يُنصح بالتخفيف من الإجهاد الحراري.",
                alert_type="temperature_high",
                threshold_value=self.temp_high,
                actual_value=weather.temperature_current,
                created_at=datetime.utcnow(),
            ))

            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.IRRIGATION,
                title="Increase Irrigation for Heat Stress",
                title_ar="زيادة الري لمواجهة الإجهاد الحراري",
                description="High temperatures increase evapotranspiration. Consider increasing irrigation frequency or applying during cooler hours.",
                description_ar="تزيد درجات الحرارة المرتفعة من التبخر النتحي. يُنصح بزيادة وتيرة الري أو الري خلال الساعات الأكثر برودة.",
                priority=8,
                urgency="urgent",
                parameters={"increase_percentage": 20, "preferred_time": "early_morning"},
                confidence_score=0.9,
                rule_source="heat_stress_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: Low humidity
        if weather.humidity and weather.humidity < self.humidity_low:
            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.IRRIGATION,
                title="Monitor for Water Stress",
                title_ar="مراقبة إجهاد المياه",
                description=f"Low humidity ({weather.humidity}%) may increase water stress. Monitor soil moisture closely.",
                description_ar=f"قد تزيد الرطوبة المنخفضة ({weather.humidity}%) من إجهاد المياه. راقب رطوبة التربة بدقة.",
                priority=5,
                urgency="normal",
                confidence_score=0.75,
                rule_source="low_humidity_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: Rain forecast
        if weather.forecast:
            rain_days = [
                f for f in weather.forecast
                if f.get("precipitation", 0) > 5
            ]
            if rain_days:
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.IRRIGATION,
                    title="Adjust Irrigation for Expected Rain",
                    title_ar="ضبط الري للأمطار المتوقعة",
                    description=f"Rain expected in the next {len(rain_days)} days. Consider reducing irrigation.",
                    description_ar=f"أمطار متوقعة خلال الـ {len(rain_days)} أيام القادمة. يُنصح بتقليل الري.",
                    priority=6,
                    urgency="normal",
                    parameters={"rain_days": len(rain_days)},
                    confidence_score=0.8,
                    rule_source="rain_forecast_rule",
                    created_at=datetime.utcnow(),
                ))

        # Rule: High wind
        if weather.wind_speed and weather.wind_speed > self.wind_high:
            alerts.append(AlertResponse(
                id=uuid4(),
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="High Wind Warning",
                title_ar="تحذير من رياح عالية",
                message=f"Wind speed is {weather.wind_speed} km/h. Avoid spraying operations.",
                message_ar=f"سرعة الرياح {weather.wind_speed} كم/ساعة. تجنب عمليات الرش.",
                alert_type="wind_high",
                threshold_value=self.wind_high,
                actual_value=weather.wind_speed,
                created_at=datetime.utcnow(),
            ))

        return recommendations, alerts

    def _run_irrigation_rules(
        self,
        context: FieldContext,
        language: str,
    ) -> List[RecommendationResponse]:
        """Run irrigation-based rules"""
        recommendations = []

        # Calculate water needs
        et0 = 0.0
        if context.weather and context.weather.evapotranspiration:
            et0 = context.weather.evapotranspiration

        soil_moisture = 50.0
        if context.soil and context.soil.moisture:
            soil_moisture = context.soil.moisture

        # Rule: Low soil moisture
        if soil_moisture < 25:
            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.IRRIGATION,
                title="Irrigation Needed - Low Soil Moisture",
                title_ar="الري مطلوب - رطوبة تربة منخفضة",
                description=f"Soil moisture is low at {soil_moisture}%. Irrigate to restore optimal moisture levels (30-60%).",
                description_ar=f"رطوبة التربة منخفضة عند {soil_moisture}%. قم بالري لاستعادة مستويات الرطوبة المثلى (30-60%).",
                priority=9,
                urgency="urgent",
                parameters={
                    "target_moisture": 45,
                    "estimated_water_mm": max(10, (45 - soil_moisture) * 0.5),
                },
                confidence_score=0.9,
                rule_source="soil_moisture_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: High ET recommendation
        if et0 > 6:
            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.IRRIGATION,
                title="High Evapotranspiration Alert",
                title_ar="تنبيه تبخر نتحي مرتفع",
                description=f"Daily ET is high at {et0:.1f}mm. Ensure irrigation covers water loss.",
                description_ar=f"التبخر النتحي اليومي مرتفع عند {et0:.1f} مم. تأكد من أن الري يغطي فقدان المياه.",
                priority=6,
                urgency="normal",
                parameters={"daily_et_mm": et0},
                confidence_score=0.85,
                rule_source="high_et_rule",
                created_at=datetime.utcnow(),
            ))

        return recommendations

    def _run_fertilization_rules(
        self,
        context: FieldContext,
        language: str,
    ) -> List[RecommendationResponse]:
        """Run fertilization-based rules"""
        recommendations = []

        if not context.soil:
            return recommendations

        soil = context.soil

        # Rule: Low nitrogen
        if soil.nitrogen and soil.nitrogen < 30:
            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.FERTILIZATION,
                title="Nitrogen Application Recommended",
                title_ar="يُنصح بإضافة النيتروجين",
                description=f"Soil nitrogen is low at {soil.nitrogen} ppm. Consider nitrogen fertilizer application.",
                description_ar=f"نيتروجين التربة منخفض عند {soil.nitrogen} جزء في المليون. يُنصح بإضافة سماد نيتروجيني.",
                priority=7,
                urgency="normal",
                parameters={"current_n_ppm": soil.nitrogen, "target_n_ppm": 50},
                confidence_score=0.8,
                rule_source="low_nitrogen_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: Low phosphorus
        if soil.phosphorus and soil.phosphorus < 15:
            recommendations.append(RecommendationResponse(
                id=uuid4(),
                type=RecommendationType.FERTILIZATION,
                title="Phosphorus Application Recommended",
                title_ar="يُنصح بإضافة الفوسفور",
                description=f"Soil phosphorus is low at {soil.phosphorus} ppm. Consider phosphorus fertilizer application.",
                description_ar=f"فوسفور التربة منخفض عند {soil.phosphorus} جزء في المليون. يُنصح بإضافة سماد فوسفوري.",
                priority=6,
                urgency="normal",
                parameters={"current_p_ppm": soil.phosphorus, "target_p_ppm": 25},
                confidence_score=0.8,
                rule_source="low_phosphorus_rule",
                created_at=datetime.utcnow(),
            ))

        # Rule: pH adjustment
        if soil.ph:
            if soil.ph < 5.5:
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.SOIL_MANAGEMENT,
                    title="Soil pH Too Acidic",
                    title_ar="درجة حموضة التربة منخفضة جداً",
                    description=f"Soil pH is {soil.ph}, which is too acidic. Consider lime application.",
                    description_ar=f"درجة حموضة التربة {soil.ph}، وهي حمضية جداً. يُنصح بإضافة الجير.",
                    priority=5,
                    urgency="low",
                    parameters={"current_ph": soil.ph, "target_ph": 6.5},
                    confidence_score=0.85,
                    rule_source="acidic_soil_rule",
                    created_at=datetime.utcnow(),
                ))
            elif soil.ph > 8.0:
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.SOIL_MANAGEMENT,
                    title="Soil pH Too Alkaline",
                    title_ar="درجة قلوية التربة مرتفعة جداً",
                    description=f"Soil pH is {soil.ph}, which is too alkaline. Consider sulfur application.",
                    description_ar=f"درجة حموضة التربة {soil.ph}، وهي قلوية جداً. يُنصح بإضافة الكبريت.",
                    priority=5,
                    urgency="low",
                    parameters={"current_ph": soil.ph, "target_ph": 7.0},
                    confidence_score=0.85,
                    rule_source="alkaline_soil_rule",
                    created_at=datetime.utcnow(),
                ))

        return recommendations

    def _run_growth_stage_rules(
        self,
        context: FieldContext,
        language: str,
    ) -> List[RecommendationResponse]:
        """Run growth stage-based rules"""
        recommendations = []

        if not context.crop:
            return recommendations

        crop = context.crop

        # Rule: Harvest readiness
        if crop.expected_harvest:
            days_to_harvest = (crop.expected_harvest - datetime.now()).days
            if 0 < days_to_harvest <= 14:
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.HARVEST,
                    title="Prepare for Harvest",
                    title_ar="التحضير للحصاد",
                    description=f"Expected harvest in {days_to_harvest} days. Prepare equipment and labor.",
                    description_ar=f"الحصاد المتوقع خلال {days_to_harvest} يوم. جهّز المعدات والعمالة.",
                    priority=8,
                    urgency="normal",
                    parameters={"days_to_harvest": days_to_harvest},
                    recommended_date=crop.expected_harvest,
                    confidence_score=0.75,
                    rule_source="harvest_preparation_rule",
                    created_at=datetime.utcnow(),
                ))

        # Rule: Growth stage specific recommendations
        if crop.growth_stage:
            if crop.growth_stage.lower() == "vegetative":
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.FERTILIZATION,
                    title="Vegetative Stage Nutrition",
                    title_ar="تغذية مرحلة النمو الخضري",
                    description="During vegetative stage, focus on nitrogen-rich fertilization to support leaf and stem growth.",
                    description_ar="خلال مرحلة النمو الخضري، ركز على التسميد الغني بالنيتروجين لدعم نمو الأوراق والسيقان.",
                    priority=5,
                    urgency="low",
                    parameters={"focus_nutrient": "nitrogen"},
                    confidence_score=0.7,
                    rule_source="vegetative_stage_rule",
                    created_at=datetime.utcnow(),
                ))
            elif crop.growth_stage.lower() == "flowering":
                recommendations.append(RecommendationResponse(
                    id=uuid4(),
                    type=RecommendationType.FERTILIZATION,
                    title="Flowering Stage Nutrition",
                    title_ar="تغذية مرحلة الإزهار",
                    description="During flowering, increase phosphorus and potassium for better flower and fruit development.",
                    description_ar="خلال مرحلة الإزهار، زد الفوسفور والبوتاسيوم لتحسين نمو الأزهار والثمار.",
                    priority=6,
                    urgency="normal",
                    parameters={"focus_nutrients": ["phosphorus", "potassium"]},
                    confidence_score=0.7,
                    rule_source="flowering_stage_rule",
                    created_at=datetime.utcnow(),
                ))

        return recommendations

    def generate_summary(
        self,
        context: FieldContext,
        health_score: float,
        risk_level: RiskLevel,
        recommendations: List[RecommendationResponse],
        alerts: List[AlertResponse],
        language: str = "en",
    ) -> Tuple[str, str]:
        """Generate analysis summary in English and Arabic"""
        # English summary
        summary_en = f"Field health score: {health_score:.0f}/100 ({risk_level.value} risk). "

        if context.ndvi:
            summary_en += f"NDVI average: {context.ndvi.mean:.2f}"
            if context.ndvi.trend:
                summary_en += f" ({context.ndvi.trend.value} trend)"
            summary_en += ". "

        if alerts:
            critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
            warnings = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
            if critical:
                summary_en += f"{critical} critical alert(s). "
            if warnings:
                summary_en += f"{warnings} warning(s). "

        summary_en += f"{len(recommendations)} recommendation(s) generated."

        # Arabic summary
        risk_ar = {"low": "منخفض", "medium": "متوسط", "high": "مرتفع", "critical": "حرج"}
        summary_ar = f"درجة صحة الحقل: {health_score:.0f}/100 (خطر {risk_ar.get(risk_level.value, risk_level.value)}). "

        if context.ndvi:
            trend_ar = {"improving": "تحسن", "stable": "مستقر", "declining": "تراجع"}
            summary_ar += f"متوسط NDVI: {context.ndvi.mean:.2f}"
            if context.ndvi.trend:
                summary_ar += f" (اتجاه {trend_ar.get(context.ndvi.trend.value, '')})"
            summary_ar += ". "

        if alerts:
            critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
            warnings = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
            if critical:
                summary_ar += f"{critical} تنبيه(ات) حرجة. "
            if warnings:
                summary_ar += f"{warnings} تحذير(ات). "

        summary_ar += f"تم إنشاء {len(recommendations)} توصية(ات)."

        return summary_en, summary_ar

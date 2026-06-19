"""
Tests for Rules Engine
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.engines.rules_engine import RulesEngine
from app.schemas.advisor import (
    FieldContext,
    NDVIContext,
    WeatherContext,
    CropContext,
    SoilContext,
    NDVITrend,
    RiskLevel,
    AlertSeverity,
    RecommendationType,
)


@pytest.fixture
def rules_engine():
    """Create rules engine instance"""
    return RulesEngine()


@pytest.fixture
def basic_context():
    """Create basic field context"""
    return FieldContext(
        field_id=uuid4(),
        field_name="Test Field",
        area_hectares=10.5,
    )


class TestHealthScoreCalculation:
    """Test health score calculation"""

    def test_healthy_ndvi_score(self, rules_engine, basic_context):
        """Test health score with healthy NDVI"""
        basic_context.ndvi = NDVIContext(
            mean=0.75,
            min=0.6,
            max=0.85,
            trend=NDVITrend.STABLE,
        )

        _, _, health_score, _ = rules_engine.analyze(basic_context)
        assert health_score >= 70

    def test_critical_ndvi_score(self, rules_engine, basic_context):
        """Test health score with critical NDVI"""
        basic_context.ndvi = NDVIContext(
            mean=0.2,
            min=0.1,
            max=0.3,
            trend=NDVITrend.DECLINING,
        )

        _, _, health_score, _ = rules_engine.analyze(basic_context)
        assert health_score < 50

    def test_declining_trend_penalty(self, rules_engine, basic_context):
        """Test that declining trend reduces score"""
        # Stable trend
        basic_context.ndvi = NDVIContext(
            mean=0.5,
            min=0.4,
            max=0.6,
            trend=NDVITrend.STABLE,
        )
        _, _, stable_score, _ = rules_engine.analyze(basic_context)

        # Declining trend
        basic_context.ndvi.trend = NDVITrend.DECLINING
        _, _, declining_score, _ = rules_engine.analyze(basic_context)

        assert declining_score < stable_score

    def test_improving_trend_bonus(self, rules_engine, basic_context):
        """Test that improving trend increases score"""
        basic_context.ndvi = NDVIContext(
            mean=0.5,
            min=0.4,
            max=0.6,
            trend=NDVITrend.STABLE,
        )
        _, _, stable_score, _ = rules_engine.analyze(basic_context)

        basic_context.ndvi.trend = NDVITrend.IMPROVING
        _, _, improving_score, _ = rules_engine.analyze(basic_context)

        assert improving_score > stable_score


class TestRiskLevelCalculation:
    """Test risk level calculation"""

    def test_low_risk_healthy_field(self, rules_engine, basic_context):
        """Test low risk for healthy field"""
        basic_context.ndvi = NDVIContext(
            mean=0.8,
            min=0.7,
            max=0.9,
            trend=NDVITrend.STABLE,
        )

        _, _, _, risk_level = rules_engine.analyze(basic_context)
        assert risk_level == RiskLevel.LOW

    def test_critical_risk_unhealthy_field(self, rules_engine, basic_context):
        """Test critical risk for unhealthy field"""
        basic_context.ndvi = NDVIContext(
            mean=0.15,
            min=0.05,
            max=0.25,
            trend=NDVITrend.DECLINING,
        )

        _, _, _, risk_level = rules_engine.analyze(basic_context)
        assert risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestNDVIRules:
    """Test NDVI-based rules"""

    def test_critical_ndvi_generates_alert(self, rules_engine, basic_context):
        """Test that critical NDVI generates alert"""
        basic_context.ndvi = NDVIContext(
            mean=0.2,
            min=0.1,
            max=0.3,
        )

        _, alerts, _, _ = rules_engine.analyze(basic_context)

        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        assert len(critical_alerts) >= 1
        assert any("ndvi" in a.alert_type.lower() for a in critical_alerts)

    def test_warning_ndvi_generates_alert(self, rules_engine, basic_context):
        """Test that warning NDVI generates alert"""
        basic_context.ndvi = NDVIContext(
            mean=0.35,
            min=0.25,
            max=0.45,
        )

        _, alerts, _, _ = rules_engine.analyze(basic_context)

        warning_alerts = [a for a in alerts if a.severity == AlertSeverity.WARNING]
        assert len(warning_alerts) >= 1

    def test_declining_trend_generates_alert(self, rules_engine, basic_context):
        """Test that declining trend generates alert"""
        basic_context.ndvi = NDVIContext(
            mean=0.5,
            min=0.4,
            max=0.6,
            trend=NDVITrend.DECLINING,
        )

        _, alerts, _, _ = rules_engine.analyze(basic_context)

        assert any("declining" in a.alert_type.lower() for a in alerts)

    def test_zone_variability_generates_recommendation(self, rules_engine, basic_context):
        """Test that high zone variability generates recommendation"""
        basic_context.ndvi = NDVIContext(
            mean=0.5,
            min=0.2,
            max=0.8,
            zones=[
                {"zone": "low", "percentage": 30, "mean_ndvi": 0.25},
                {"zone": "high", "percentage": 70, "mean_ndvi": 0.7},
            ],
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        assert any("zone" in r.title.lower() for r in recs)


class TestWeatherRules:
    """Test weather-based rules"""

    def test_high_temperature_alert(self, rules_engine, basic_context):
        """Test that high temperature generates alert"""
        basic_context.weather = WeatherContext(
            temperature_current=42.0,
        )

        _, alerts, _, _ = rules_engine.analyze(basic_context)

        assert any("temperature" in a.alert_type.lower() for a in alerts)

    def test_high_temperature_irrigation_recommendation(self, rules_engine, basic_context):
        """Test that high temp generates irrigation recommendation"""
        basic_context.weather = WeatherContext(
            temperature_current=42.0,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        irrigation_recs = [r for r in recs if r.type == RecommendationType.IRRIGATION]
        assert len(irrigation_recs) >= 1

    def test_rain_forecast_recommendation(self, rules_engine, basic_context):
        """Test rain forecast generates recommendation"""
        basic_context.weather = WeatherContext(
            temperature_current=28.0,
            forecast=[
                {"date": "2025-12-03", "precipitation": 10},
                {"date": "2025-12-04", "precipitation": 15},
            ],
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        assert any("rain" in r.title.lower() for r in recs)

    def test_high_wind_alert(self, rules_engine, basic_context):
        """Test that high wind generates alert"""
        basic_context.weather = WeatherContext(
            wind_speed=55.0,
        )

        _, alerts, _, _ = rules_engine.analyze(basic_context)

        assert any("wind" in a.alert_type.lower() for a in alerts)


class TestIrrigationRules:
    """Test irrigation rules"""

    def test_low_soil_moisture_recommendation(self, rules_engine, basic_context):
        """Test low soil moisture generates irrigation recommendation"""
        basic_context.soil = SoilContext(
            moisture=20.0,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        irrigation_recs = [r for r in recs if r.type == RecommendationType.IRRIGATION]
        urgent_recs = [r for r in irrigation_recs if r.urgency == "urgent"]
        assert len(urgent_recs) >= 1

    def test_high_et_recommendation(self, rules_engine, basic_context):
        """Test high ET generates recommendation"""
        basic_context.weather = WeatherContext(
            evapotranspiration=7.5,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        assert any("et" in r.title.lower() or "evapotranspiration" in r.title.lower()
                   for r in recs)


class TestFertilizationRules:
    """Test fertilization rules"""

    def test_low_nitrogen_recommendation(self, rules_engine, basic_context):
        """Test low nitrogen generates recommendation"""
        basic_context.soil = SoilContext(
            nitrogen=20.0,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        fert_recs = [r for r in recs if r.type == RecommendationType.FERTILIZATION]
        assert any("nitrogen" in r.title.lower() for r in fert_recs)

    def test_low_phosphorus_recommendation(self, rules_engine, basic_context):
        """Test low phosphorus generates recommendation"""
        basic_context.soil = SoilContext(
            phosphorus=10.0,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        fert_recs = [r for r in recs if r.type == RecommendationType.FERTILIZATION]
        assert any("phosphorus" in r.title.lower() for r in fert_recs)

    def test_acidic_soil_recommendation(self, rules_engine, basic_context):
        """Test acidic soil generates recommendation"""
        basic_context.soil = SoilContext(
            ph=5.0,
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        soil_recs = [r for r in recs if r.type == RecommendationType.SOIL_MANAGEMENT]
        assert any("acidic" in r.title.lower() or "ph" in r.title.lower()
                   for r in soil_recs)


class TestGrowthStageRules:
    """Test growth stage rules"""

    def test_harvest_preparation_recommendation(self, rules_engine, basic_context):
        """Test harvest preparation recommendation"""
        basic_context.crop = CropContext(
            crop_type="wheat",
            growth_stage="maturity",
            expected_harvest=datetime.now() + timedelta(days=10),
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        harvest_recs = [r for r in recs if r.type == RecommendationType.HARVEST]
        assert len(harvest_recs) >= 1

    def test_vegetative_stage_nutrition(self, rules_engine, basic_context):
        """Test vegetative stage nutrition recommendation"""
        basic_context.crop = CropContext(
            crop_type="wheat",
            growth_stage="vegetative",
        )

        recs, _, _, _ = rules_engine.analyze(basic_context)

        # Should recommend nitrogen focus
        assert any("vegetative" in r.title.lower() or "nitrogen" in str(r.parameters).lower()
                   for r in recs)


class TestSummaryGeneration:
    """Test summary generation"""

    def test_english_summary(self, rules_engine, basic_context):
        """Test English summary generation"""
        basic_context.ndvi = NDVIContext(mean=0.5, min=0.3, max=0.7)

        recs, alerts, health_score, risk_level = rules_engine.analyze(basic_context)
        summary_en, summary_ar = rules_engine.generate_summary(
            basic_context, health_score, risk_level, recs, alerts, "en"
        )

        assert "health score" in summary_en.lower()
        assert str(int(health_score)) in summary_en

    def test_arabic_summary(self, rules_engine, basic_context):
        """Test Arabic summary generation"""
        basic_context.ndvi = NDVIContext(mean=0.5, min=0.3, max=0.7)

        recs, alerts, health_score, risk_level = rules_engine.analyze(basic_context)
        summary_en, summary_ar = rules_engine.generate_summary(
            basic_context, health_score, risk_level, recs, alerts, "ar"
        )

        assert "صحة" in summary_ar  # Health in Arabic
        assert str(int(health_score)) in summary_ar

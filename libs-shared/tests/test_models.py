"""
Tests for SQLAlchemy ORM Models
اختبارات نماذج قاعدة البيانات
"""

import pytest
from datetime import date, datetime
from uuid import uuid4

from sahool_shared.models import (
    Region, Farmer, Field, NDVIResult, WeatherData, Alert, User, Tenant
)
from sahool_shared.models.alert import AlertSeverity, AlertType, AlertStatus
from sahool_shared.models.user import UserRole, TenantPlan


class TestRegionModel:
    """Tests for Region model."""

    def test_region_display_name_with_english(self):
        """Test bilingual display name."""
        region = Region(
            id=1,
            name_ar="صنعاء",
            name_en="Sanaa"
        )
        assert region.display_name == "صنعاء (Sanaa)"

    def test_region_display_name_arabic_only(self):
        """Test Arabic-only display name."""
        region = Region(
            id=1,
            name_ar="تعز"
        )
        assert region.display_name == "تعز"


class TestFarmerModel:
    """Tests for Farmer model."""

    def test_farmer_total_fields_empty(self):
        """Test total fields when no fields."""
        farmer = Farmer(
            id=uuid4(),
            name="أحمد محمد",
            tenant_id=uuid4()
        )
        farmer.fields = []
        assert farmer.total_fields == 0

    def test_farmer_repr(self):
        """Test farmer string representation."""
        farmer_id = uuid4()
        farmer = Farmer(
            id=farmer_id,
            name="علي أحمد",
            tenant_id=uuid4()
        )
        assert "علي أحمد" in repr(farmer)


class TestFieldModel:
    """Tests for Field model."""

    def test_field_health_status_excellent(self):
        """Test excellent health status."""
        field = Field(
            id=uuid4(),
            tenant_id=uuid4(),
            name_ar="حقل القمح",
            area_hectares=10.0
        )
        field.ndvi_results = []

        # Mock NDVI result
        ndvi = NDVIResult(
            id=uuid4(),
            field_id=field.id,
            tenant_id=field.tenant_id,
            ndvi_value=0.75,
            acquisition_date=date.today()
        )
        field.ndvi_results = [ndvi]

        assert field.latest_ndvi == 0.75
        assert field.health_status == "excellent"

    def test_field_health_status_unknown(self):
        """Test unknown health status when no NDVI."""
        field = Field(
            id=uuid4(),
            tenant_id=uuid4(),
            name_ar="حقل جديد",
            area_hectares=5.0
        )
        field.ndvi_results = []

        assert field.latest_ndvi is None
        assert field.health_status == "unknown"


class TestNDVIResultModel:
    """Tests for NDVIResult model."""

    @pytest.mark.parametrize("ndvi,expected", [
        (0.7, "ممتاز"),
        (0.5, "جيد"),
        (0.3, "متوسط"),
        (0.1, "ضعيف"),
        (-0.1, "غير مزروع"),
    ])
    def test_ndvi_health_category(self, ndvi, expected):
        """Test NDVI health category in Arabic."""
        result = NDVIResult(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            ndvi_value=ndvi,
            acquisition_date=date.today()
        )
        assert result.health_category == expected

    def test_ndvi_high_quality(self):
        """Test high quality NDVI result."""
        result = NDVIResult(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            ndvi_value=0.6,
            acquisition_date=date.today(),
            cloud_coverage=10.0
        )
        assert result.is_high_quality is True

    def test_ndvi_low_quality(self):
        """Test low quality NDVI result."""
        result = NDVIResult(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            ndvi_value=0.6,
            acquisition_date=date.today(),
            cloud_coverage=30.0
        )
        assert result.is_high_quality is False


class TestWeatherDataModel:
    """Tests for WeatherData model."""

    def test_favorable_weather(self):
        """Test favorable weather conditions."""
        weather = WeatherData(
            id=uuid4(),
            tenant_id=uuid4(),
            temperature=25.0,
            humidity=60.0,
            wind_speed=5.0
        )
        assert weather.is_favorable_for_agriculture is True

    def test_unfavorable_hot_weather(self):
        """Test unfavorable hot weather."""
        weather = WeatherData(
            id=uuid4(),
            tenant_id=uuid4(),
            temperature=42.0,
            humidity=50.0,
            wind_speed=3.0
        )
        assert weather.is_favorable_for_agriculture is False

    def test_alert_conditions_heat(self):
        """Test heat alert condition."""
        weather = WeatherData(
            id=uuid4(),
            tenant_id=uuid4(),
            temperature=45.0
        )
        alerts = weather.alert_conditions
        assert "حرارة شديدة" in alerts

    def test_alert_conditions_wind(self):
        """Test wind alert condition."""
        weather = WeatherData(
            id=uuid4(),
            tenant_id=uuid4(),
            temperature=25.0,
            wind_speed=20.0
        )
        alerts = weather.alert_conditions
        assert "رياح قوية" in alerts


class TestAlertModel:
    """Tests for Alert model."""

    def test_alert_acknowledge(self):
        """Test alert acknowledgement."""
        alert = Alert(
            id=uuid4(),
            tenant_id=uuid4(),
            title_ar="تنبيه طقس",
            message_ar="درجة حرارة عالية متوقعة",
            alert_type=AlertType.WEATHER.value,
            severity=AlertSeverity.HIGH.value
        )
        alert.acknowledge()

        assert alert.status == AlertStatus.ACKNOWLEDGED.value
        assert alert.acknowledged_at is not None

    def test_alert_resolve(self):
        """Test alert resolution."""
        alert = Alert(
            id=uuid4(),
            tenant_id=uuid4(),
            title_ar="تنبيه",
            message_ar="رسالة"
        )
        alert.resolve()

        assert alert.status == AlertStatus.RESOLVED.value
        assert alert.resolved_at is not None

    def test_alert_is_active(self):
        """Test alert active status."""
        alert = Alert(
            id=uuid4(),
            tenant_id=uuid4(),
            title_ar="تنبيه نشط",
            message_ar="رسالة",
            status=AlertStatus.ACTIVE.value
        )
        assert alert.is_active is True


class TestUserModel:
    """Tests for User model."""

    def test_user_has_permission_admin(self):
        """Test admin has all permissions."""
        user = User(
            id=uuid4(),
            email="admin@sahool.ye",
            password_hash="hash",
            full_name="مدير النظام",
            role=UserRole.ADMIN.value,
            tenant_id=uuid4()
        )
        assert user.has_permission("any_permission") is True

    def test_user_has_permission_specific(self):
        """Test specific permission check."""
        user = User(
            id=uuid4(),
            email="user@sahool.ye",
            password_hash="hash",
            full_name="مستخدم",
            role=UserRole.VIEWER.value,
            tenant_id=uuid4(),
            permissions={"view_fields": True, "edit_fields": False}
        )
        assert user.has_permission("view_fields") is True
        assert user.has_permission("edit_fields") is False


class TestTenantModel:
    """Tests for Tenant model."""

    def test_tenant_plan_active(self):
        """Test active tenant plan."""
        tenant = Tenant(
            id=uuid4(),
            name="مزرعة السعادة",
            slug="farm-happiness",
            plan=TenantPlan.PROFESSIONAL.value,
            is_active=True
        )
        assert tenant.is_plan_active is True

    def test_tenant_plan_inactive(self):
        """Test inactive tenant."""
        tenant = Tenant(
            id=uuid4(),
            name="مزرعة قديمة",
            slug="old-farm",
            is_active=False
        )
        assert tenant.is_plan_active is False

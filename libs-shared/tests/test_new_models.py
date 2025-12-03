"""
Tests for New SQLAlchemy ORM Models
اختبارات النماذج الجديدة لقاعدة البيانات
"""

import pytest
from datetime import date, datetime
from uuid import uuid4

from sahool_shared.models import (
    SoilAnalysis, YieldRecord, IrrigationSchedule, PlantHealth, AuditLog
)


class TestSoilAnalysisModel:
    """Tests for SoilAnalysis model."""

    def test_soil_fertility_excellent(self):
        """Test excellent fertility status."""
        soil = SoilAnalysis(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            nitrogen_ppm=150.0,
            phosphorus_ppm=120.0,
            potassium_ppm=130.0
        )
        assert soil.fertility_status == "excellent"

    def test_soil_fertility_good(self):
        """Test good fertility status."""
        soil = SoilAnalysis(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            nitrogen_ppm=70.0,
            phosphorus_ppm=60.0,
            potassium_ppm=55.0
        )
        assert soil.fertility_status == "good"

    def test_soil_fertility_moderate(self):
        """Test moderate fertility status."""
        soil = SoilAnalysis(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            nitrogen_ppm=30.0,
            phosphorus_ppm=35.0,
            potassium_ppm=25.0
        )
        assert soil.fertility_status == "moderate"

    def test_soil_fertility_poor(self):
        """Test poor fertility status."""
        soil = SoilAnalysis(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            nitrogen_ppm=10.0,
            phosphorus_ppm=15.0,
            potassium_ppm=12.0
        )
        assert soil.fertility_status == "poor"

    def test_soil_fertility_unknown(self):
        """Test unknown fertility when missing data."""
        soil = SoilAnalysis(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            ph_value=6.5
        )
        assert soil.fertility_status == "unknown"

    def test_soil_repr(self):
        """Test soil analysis string representation."""
        soil_id = uuid4()
        field_id = uuid4()
        soil = SoilAnalysis(
            id=soil_id,
            field_id=field_id,
            tenant_id=uuid4()
        )
        assert str(soil_id) in repr(soil)
        assert str(field_id) in repr(soil)


class TestYieldRecordModel:
    """Tests for YieldRecord model."""

    def test_profit_margin_calculation(self):
        """Test profit margin calculation."""
        record = YieldRecord(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            crop_type="قمح",
            year=2024,
            revenue_yer=1000000.0,
            expenses_yer=600000.0,
            profit_yer=400000.0
        )
        assert record.profit_margin == 40.0

    def test_profit_margin_no_revenue(self):
        """Test profit margin when no revenue."""
        record = YieldRecord(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            crop_type="ذرة",
            year=2024
        )
        assert record.profit_margin is None

    def test_profit_margin_zero_revenue(self):
        """Test profit margin with zero revenue."""
        record = YieldRecord(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            crop_type="شعير",
            year=2024,
            revenue_yer=0.0,
            profit_yer=0.0
        )
        assert record.profit_margin is None

    def test_yield_record_repr(self):
        """Test yield record string representation."""
        record = YieldRecord(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            crop_type="قهوة",
            year=2024
        )
        assert "قهوة" in repr(record)
        assert "2024" in repr(record)


class TestIrrigationScheduleModel:
    """Tests for IrrigationSchedule model."""

    def test_mark_completed(self):
        """Test marking irrigation as completed."""
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=date.today(),
            status="pending"
        )
        schedule.mark_completed()

        assert schedule.status == "completed"
        assert schedule.executed_at is not None

    def test_mark_cancelled(self):
        """Test marking irrigation as cancelled."""
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=date.today(),
            status="pending"
        )
        schedule.mark_cancelled()

        assert schedule.status == "cancelled"

    def test_is_overdue_true(self):
        """Test overdue irrigation detection."""
        from datetime import timedelta
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=date.today() - timedelta(days=2),
            status="pending"
        )
        assert schedule.is_overdue is True

    def test_is_overdue_false_completed(self):
        """Test non-overdue completed irrigation."""
        from datetime import timedelta
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=date.today() - timedelta(days=2),
            status="completed"
        )
        assert schedule.is_overdue is False

    def test_is_overdue_false_future(self):
        """Test non-overdue future irrigation."""
        from datetime import timedelta
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=date.today() + timedelta(days=2),
            status="pending"
        )
        assert schedule.is_overdue is False

    def test_irrigation_repr(self):
        """Test irrigation schedule string representation."""
        today = date.today()
        schedule = IrrigationSchedule(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            schedule_date=today,
            status="pending"
        )
        assert str(today) in repr(schedule)
        assert "pending" in repr(schedule)


class TestPlantHealthModel:
    """Tests for PlantHealth model."""

    def test_mark_resolved(self):
        """Test marking health issue as resolved."""
        health = PlantHealth(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            disease_name="Leaf Blight",
            severity_level="high",
            is_resolved=False
        )
        health.mark_resolved()

        assert health.is_resolved is True
        assert health.resolved_at is not None

    def test_is_critical_high(self):
        """Test critical detection for high severity."""
        health = PlantHealth(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            severity_level="high"
        )
        assert health.is_critical is True

    def test_is_critical_critical(self):
        """Test critical detection for critical severity."""
        health = PlantHealth(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            severity_level="critical"
        )
        assert health.is_critical is True

    def test_is_critical_false(self):
        """Test non-critical for low severity."""
        health = PlantHealth(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            severity_level="low"
        )
        assert health.is_critical is False

    def test_plant_health_repr(self):
        """Test plant health string representation."""
        health = PlantHealth(
            id=uuid4(),
            field_id=uuid4(),
            tenant_id=uuid4(),
            disease_name="Rust",
            severity_level="medium"
        )
        assert "Rust" in repr(health)
        assert "medium" in repr(health)


class TestAuditLogModel:
    """Tests for AuditLog model."""

    def test_create_log_factory(self):
        """Test audit log factory method."""
        tenant_id = uuid4()
        log = AuditLog.create_log(
            tenant_id=tenant_id,
            action="create",
            user_id="user123",
            table_name="fields",
            record_id=uuid4(),
            new_values={"name": "حقل جديد"}
        )

        assert log.tenant_id == tenant_id
        assert log.action == "create"
        assert log.user_id == "user123"
        assert log.table_name == "fields"
        assert log.new_values["name"] == "حقل جديد"

    def test_audit_log_repr(self):
        """Test audit log string representation."""
        log = AuditLog(
            id=uuid4(),
            tenant_id=uuid4(),
            action="update",
            table_name="farmers"
        )
        assert "update" in repr(log)
        assert "farmers" in repr(log)

    def test_audit_log_with_old_values(self):
        """Test audit log with old and new values."""
        log = AuditLog.create_log(
            tenant_id=uuid4(),
            action="update",
            old_values={"name": "اسم قديم"},
            new_values={"name": "اسم جديد"}
        )
        assert log.old_values["name"] == "اسم قديم"
        assert log.new_values["name"] == "اسم جديد"

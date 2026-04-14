"""
Event Type Definitions
تعريفات أنواع الأحداث
"""

from typing import Any, Dict, Optional
from datetime import date

from sahool_shared.events.event_bus import Event


class FieldCreatedEvent(Event):
    """Event emitted when a new field is created."""
    type: str = "field.created"

    @classmethod
    def create(
        cls,
        field_id: str,
        farmer_id: str,
        tenant_id: str,
        name: str,
        area_hectares: float,
        crop_type: Optional[str] = None,
        source: str = "field-service",
    ) -> "FieldCreatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "field_id": field_id,
                "farmer_id": farmer_id,
                "name": name,
                "area_hectares": area_hectares,
                "crop_type": crop_type,
            }
        )


class FieldUpdatedEvent(Event):
    """Event emitted when a field is updated."""
    type: str = "field.updated"

    @classmethod
    def create(
        cls,
        field_id: str,
        tenant_id: str,
        changes: Dict[str, Any],
        source: str = "field-service",
    ) -> "FieldUpdatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "field_id": field_id,
                "changes": changes,
            }
        )


class NDVIProcessedEvent(Event):
    """Event emitted when NDVI data is processed."""
    type: str = "ndvi.processed"

    @classmethod
    def create(
        cls,
        field_id: str,
        tenant_id: str,
        ndvi_value: float,
        acquisition_date: date,
        satellite: str = "Sentinel-2",
        source: str = "ndvi-processor",
    ) -> "NDVIProcessedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "field_id": field_id,
                "ndvi_value": ndvi_value,
                "acquisition_date": acquisition_date.isoformat(),
                "satellite": satellite,
                "health_category": cls._get_health_category(ndvi_value),
            }
        )

    @staticmethod
    def _get_health_category(ndvi: float) -> str:
        if ndvi >= 0.6:
            return "excellent"
        if ndvi >= 0.4:
            return "good"
        if ndvi >= 0.2:
            return "moderate"
        if ndvi >= 0:
            return "poor"
        return "bare"


class WeatherUpdatedEvent(Event):
    """Event emitted when weather data is updated."""
    type: str = "weather.updated"

    @classmethod
    def create(
        cls,
        region_id: Optional[int],
        field_id: Optional[str],
        tenant_id: str,
        temperature: float,
        humidity: float,
        rainfall: float,
        forecast_date: date,
        source: str = "weather-ingestor",
    ) -> "WeatherUpdatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "region_id": region_id,
                "field_id": field_id,
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall,
                "forecast_date": forecast_date.isoformat(),
            }
        )


class AlertCreatedEvent(Event):
    """Event emitted when an alert is created."""
    type: str = "alert.created"

    @classmethod
    def create(
        cls,
        alert_id: str,
        tenant_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        field_id: Optional[str] = None,
        region_id: Optional[int] = None,
        source: str = "alert-service",
    ) -> "AlertCreatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "alert_id": alert_id,
                "alert_type": alert_type,
                "severity": severity,
                "title": title,
                "message": message,
                "field_id": field_id,
                "region_id": region_id,
            }
        )


class UserCreatedEvent(Event):
    """Event emitted when a user is created."""
    type: str = "user.created"

    @classmethod
    def create(
        cls,
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        source: str = "platform-core",
    ) -> "UserCreatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "user_id": user_id,
                "email": email,
                "role": role,
            }
        )


class TenantCreatedEvent(Event):
    """Event emitted when a tenant is created."""
    type: str = "tenant.created"

    @classmethod
    def create(
        cls,
        tenant_id: str,
        name: str,
        plan: str,
        source: str = "platform-core",
    ) -> "TenantCreatedEvent":
        return cls(
            tenant_id=tenant_id,
            source=source,
            data={
                "name": name,
                "plan": plan,
            }
        )

"""
Pydantic schemas for Advisor API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


# ==================== Enums ====================

class RecommendationType(str, Enum):
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    DISEASE_TREATMENT = "disease_treatment"
    HARVEST = "harvest"
    SOIL_MANAGEMENT = "soil_management"
    GENERAL = "general"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ActionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NDVITrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


# ==================== Context Schemas ====================

class NDVIContext(BaseModel):
    """NDVI data context"""
    mean: float = Field(..., ge=-1.0, le=1.0, description="Mean NDVI value")
    min: float = Field(..., ge=-1.0, le=1.0, description="Minimum NDVI value")
    max: float = Field(..., ge=-1.0, le=1.0, description="Maximum NDVI value")
    std_dev: Optional[float] = Field(None, description="Standard deviation")
    acquisition_date: Optional[datetime] = None
    trend: Optional[NDVITrend] = None
    zones: Optional[List[Dict[str, Any]]] = Field(default=[], description="NDVI zones data")
    history: Optional[List[Dict[str, Any]]] = Field(default=[], description="Historical NDVI data")


class WeatherContext(BaseModel):
    """Weather data context"""
    temperature_current: Optional[float] = Field(None, description="Current temperature (C)")
    temperature_min: Optional[float] = Field(None, description="Min temperature (C)")
    temperature_max: Optional[float] = Field(None, description="Max temperature (C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity (%)")
    precipitation: Optional[float] = Field(None, ge=0, description="Precipitation (mm)")
    precipitation_7d: Optional[float] = Field(None, description="7-day precipitation (mm)")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed (km/h)")
    uv_index: Optional[float] = Field(None, ge=0, description="UV index")
    evapotranspiration: Optional[float] = Field(None, description="ET (mm/day)")
    forecast: Optional[List[Dict[str, Any]]] = Field(default=[], description="Weather forecast")


class CropContext(BaseModel):
    """Crop information context"""
    crop_type: Optional[str] = Field(None, description="Type of crop")
    growth_stage: Optional[str] = Field(None, description="Current growth stage")
    planting_date: Optional[datetime] = None
    expected_harvest: Optional[datetime] = None
    variety: Optional[str] = None
    irrigation_type: Optional[str] = None  # drip, sprinkler, flood, rainfed


class SoilContext(BaseModel):
    """Soil information context"""
    soil_type: Optional[str] = None
    ph: Optional[float] = Field(None, ge=0, le=14)
    organic_matter: Optional[float] = Field(None, ge=0, le=100, description="Organic matter (%)")
    nitrogen: Optional[float] = Field(None, description="Nitrogen level (ppm)")
    phosphorus: Optional[float] = Field(None, description="Phosphorus level (ppm)")
    potassium: Optional[float] = Field(None, description="Potassium level (ppm)")
    moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture (%)")
    last_test_date: Optional[datetime] = None


class FieldContext(BaseModel):
    """Complete field context for analysis"""
    field_id: UUID
    field_name: Optional[str] = None
    area_hectares: Optional[float] = None
    location: Optional[Dict[str, float]] = None  # {"lat": ..., "lng": ...}

    ndvi: Optional[NDVIContext] = None
    weather: Optional[WeatherContext] = None
    crop: Optional[CropContext] = None
    soil: Optional[SoilContext] = None

    # Historical data
    previous_issues: Optional[List[str]] = Field(default=[])
    previous_recommendations: Optional[List[str]] = Field(default=[])


# ==================== Request Schemas ====================

class AnalyzeFieldRequest(BaseModel):
    """Request to analyze a field"""
    field_id: UUID
    tenant_id: Optional[UUID] = None
    include_weather: bool = Field(True, description="Include weather data in analysis")
    include_forecast: bool = Field(True, description="Include weather forecast")
    analysis_depth: str = Field("standard", description="Analysis depth: quick, standard, deep")
    language: str = Field("en", description="Response language: en, ar")

    # Optional overrides
    ndvi_data: Optional[NDVIContext] = None
    weather_data: Optional[WeatherContext] = None
    crop_data: Optional[CropContext] = None
    soil_data: Optional[SoilContext] = None


class PlaybookRequest(BaseModel):
    """Request for action playbook"""
    field_id: UUID
    recommendation_ids: Optional[List[UUID]] = None
    time_horizon_days: int = Field(14, ge=1, le=90, description="Planning horizon in days")
    include_resources: bool = Field(True, description="Include resource estimates")


# ==================== Response Schemas ====================

class RecommendationResponse(BaseModel):
    """Single recommendation response"""
    id: UUID
    type: RecommendationType
    title: str
    title_ar: Optional[str] = None
    description: str
    description_ar: Optional[str] = None
    priority: int = Field(..., ge=1, le=10)
    urgency: str
    recommended_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    affected_zones: Optional[List[str]] = None
    confidence_score: float = Field(..., ge=0, le=1)
    rule_source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Single alert response"""
    id: UUID
    severity: AlertSeverity
    status: AlertStatus
    title: str
    title_ar: Optional[str] = None
    message: str
    message_ar: Optional[str] = None
    alert_type: str
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    affected_zones: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyzeFieldResponse(BaseModel):
    """Response from field analysis"""
    session_id: UUID
    field_id: UUID
    analysis_date: datetime

    # Health Assessment
    health_score: float = Field(..., ge=0, le=100, description="Overall health score")
    risk_level: RiskLevel
    ndvi_trend: Optional[NDVITrend] = None

    # Summary
    summary: str
    summary_ar: Optional[str] = None

    # Context used
    context: FieldContext

    # Results
    recommendations: List[RecommendationResponse]
    alerts: List[AlertResponse]

    # Statistics
    recommendation_count: int
    alert_count: int
    critical_alerts: int


class PlaybookAction(BaseModel):
    """Single action in playbook"""
    order: int
    recommendation_id: UUID
    action_type: str
    title: str
    title_ar: Optional[str] = None
    description: str
    description_ar: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    duration_hours: Optional[float] = None
    resources: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[UUID]] = None
    notes: Optional[str] = None


class PlaybookResponse(BaseModel):
    """Action playbook response"""
    field_id: UUID
    generated_at: datetime
    time_horizon_days: int
    actions: List[PlaybookAction]
    total_estimated_hours: Optional[float] = None
    resource_summary: Optional[Dict[str, Any]] = None
    calendar_view: Optional[List[Dict[str, Any]]] = None


class ActionLogCreate(BaseModel):
    """Create action log entry"""
    recommendation_id: UUID
    action_type: str
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    performer_notes: Optional[str] = None


class ActionLogResponse(BaseModel):
    """Action log response"""
    id: UUID
    recommendation_id: UUID
    field_id: UUID
    status: ActionStatus
    action_type: str
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    database: str = "unknown"
    dependencies: Dict[str, str] = {}

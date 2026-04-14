#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 3: Backend Models - Field, NDVI, Advisor
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء نماذج قاعدة البيانات..."

# ─────────────────────────────────────────────────────────────────────────────
# Field Model
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/models/field.py" << 'EOF'
"""
Field Model
نموذج الحقل
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.core.database import Base


class Field(Base):
    """Agricultural field model"""
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    crop_type = Column(String(100), nullable=True)
    crop_variety = Column(String(100), nullable=True)

    # Geometry
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    area_ha = Column(Float, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)

    # Dates
    planting_date = Column(DateTime(timezone=True), nullable=True)
    expected_harvest_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(50), default="active")
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="fields")
    ndvi_results = relationship("NDVIResult", back_populates="field", cascade="all, delete-orphan")
    advisor_sessions = relationship("AdvisorSession", back_populates="field", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_field_tenant_status", "tenant_id", "status"),
        Index("idx_field_crop_type", "crop_type"),
    )

    def __repr__(self):
        return f"<Field {self.name} ({self.id})>"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# NDVI Model
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/models/ndvi.py" << 'EOF'
"""
NDVI Result Model
نموذج نتائج NDVI
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class NDVIResult(Base):
    """NDVI analysis result"""
    __tablename__ = "ndvi_results"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, nullable=False, index=True)

    # Analysis date
    analysis_date = Column(Date, nullable=False, index=True)
    satellite_source = Column(String(50), default="sentinel-2")
    cloud_coverage = Column(Float, nullable=True)

    # NDVI Statistics
    mean_ndvi = Column(Float, nullable=False)
    min_ndvi = Column(Float, nullable=True)
    max_ndvi = Column(Float, nullable=True)
    std_ndvi = Column(Float, nullable=True)
    median_ndvi = Column(Float, nullable=True)

    # Pixel info
    pixel_count = Column(Integer, nullable=True)
    valid_pixel_percentage = Column(Float, nullable=True)

    # Zone analysis
    zones = Column(JSON, nullable=True)  # {"low": 20, "medium": 50, "high": 30}

    # Tile URL for visualization
    tile_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Metadata
    processing_time_ms = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    field = relationship("Field", back_populates="ndvi_results")

    # Indexes
    __table_args__ = (
        Index("idx_ndvi_field_date", "field_id", "analysis_date"),
        Index("idx_ndvi_tenant_date", "tenant_id", "analysis_date"),
    )

    def __repr__(self):
        return f"<NDVIResult field={self.field_id} date={self.analysis_date}>"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Advisor Models
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/models/advisor.py" << 'EOF'
"""
Advisor Models
نماذج المستشار الزراعي
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid

from app.core.database import Base


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    EXPIRED = "expired"


class AlertType(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


class AdvisorSession(Base):
    """Advisor analysis session"""
    __tablename__ = "advisor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, nullable=False, index=True)

    # Session info
    session_type = Column(String(50), default="full_analysis")
    status = Column(String(20), default="completed")

    # Context data
    ndvi_context = Column(JSON, nullable=True)
    weather_context = Column(JSON, nullable=True)
    crop_context = Column(JSON, nullable=True)
    soil_context = Column(JSON, nullable=True)

    # Overall scores
    health_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    field = relationship("Field", back_populates="advisor_sessions")
    recommendations = relationship("Recommendation", back_populates="session", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AdvisorSession {self.uuid}>"


class Recommendation(Base):
    """Agricultural recommendation"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(Integer, ForeignKey("advisor_sessions.id", ondelete="CASCADE"), nullable=False)
    field_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)

    # Rule info
    rule_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # irrigation, fertilization, pest_control, harvest

    # Priority and status
    priority = Column(SQLEnum(RecommendationPriority), default=RecommendationPriority.MEDIUM)
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.PENDING)

    # Content (bilingual)
    title_ar = Column(String(255), nullable=False)
    title_en = Column(String(255), nullable=False)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    # Actions
    actions = Column(JSON, nullable=True)  # List of action items

    # Scoring
    confidence_score = Column(Float, default=0.8)
    impact_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("AdvisorSession", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation {self.rule_name} ({self.priority.value})>"


class Alert(Base):
    """System alert"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(Integer, ForeignKey("advisor_sessions.id", ondelete="SET NULL"), nullable=True)
    field_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)

    # Alert info
    alert_type = Column(SQLEnum(AlertType), default=AlertType.INFO)
    category = Column(String(50), nullable=False)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)

    # Status
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("AdvisorSession", back_populates="alerts")

    def __repr__(self):
        return f"<Alert {self.alert_type.value}: {self.title}>"


class ActionLog(Base):
    """Log of actions taken on recommendations"""
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    field_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True)

    # Action info
    action_type = Column(String(50), nullable=False)  # accepted, rejected, completed, deferred
    notes = Column(Text, nullable=True)
    result = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ActionLog {self.action_type} for rec={self.recommendation_id}>"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Models __init__
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/models/__init__.py" << 'EOF'
"""
Database Models
نماذج قاعدة البيانات
"""
from app.models.user import User, RefreshToken, UserRole
from app.models.field import Field
from app.models.ndvi import NDVIResult
from app.models.advisor import (
    AdvisorSession,
    Recommendation,
    Alert,
    ActionLog,
    RecommendationPriority,
    RecommendationStatus,
    AlertType
)

__all__ = [
    "User",
    "RefreshToken",
    "UserRole",
    "Field",
    "NDVIResult",
    "AdvisorSession",
    "Recommendation",
    "Alert",
    "ActionLog",
    "RecommendationPriority",
    "RecommendationStatus",
    "AlertType",
]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Schemas - Field
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/schemas/field.py" << 'EOF'
"""
Field Schemas
مخططات الحقل
"""
from pydantic import BaseModel, Field as PydanticField
from typing import Optional, Dict, Any, List
from datetime import datetime
from geojson_pydantic import Polygon


class FieldCreate(BaseModel):
    """Schema for creating a field"""
    name: str = PydanticField(..., min_length=1, max_length=255)
    description: Optional[str] = None
    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    geometry: Dict[str, Any]  # GeoJSON Polygon
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class FieldUpdate(BaseModel):
    """Schema for updating a field"""
    name: Optional[str] = PydanticField(None, min_length=1, max_length=255)
    description: Optional[str] = None
    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FieldResponse(BaseModel):
    """Schema for field response"""
    id: int
    uuid: str
    tenant_id: int
    name: str
    description: Optional[str]
    crop_type: Optional[str]
    crop_variety: Optional[str]
    geometry: Dict[str, Any]
    area_ha: Optional[float]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    planting_date: Optional[datetime]
    expected_harvest_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FieldListResponse(BaseModel):
    """Schema for paginated field list"""
    items: List[FieldResponse]
    total: int
    page: int
    page_size: int
    pages: int
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Schemas - NDVI
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/schemas/ndvi.py" << 'EOF'
"""
NDVI Schemas
مخططات NDVI
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import date, datetime


class NDVIZone(BaseModel):
    """Zone statistics"""
    percentage: float
    area_ha: float
    pixel_count: int


class NDVIZones(BaseModel):
    """NDVI zones breakdown"""
    critical: Optional[NDVIZone] = None  # < 0.2
    low: Optional[NDVIZone] = None       # 0.2 - 0.4
    medium: Optional[NDVIZone] = None    # 0.4 - 0.6
    high: Optional[NDVIZone] = None      # 0.6 - 0.8
    very_high: Optional[NDVIZone] = None # > 0.8


class NDVIResponse(BaseModel):
    """NDVI analysis response"""
    id: int
    field_id: int
    analysis_date: date
    satellite_source: str
    cloud_coverage: Optional[float]

    # Statistics
    mean_ndvi: float
    min_ndvi: Optional[float]
    max_ndvi: Optional[float]
    std_ndvi: Optional[float]
    median_ndvi: Optional[float]

    # Zones
    zones: Optional[NDVIZones]

    # Visualization
    tile_url: Optional[str]
    thumbnail_url: Optional[str]

    # Meta
    pixel_count: Optional[int]
    processing_time_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class NDVITimelineResponse(BaseModel):
    """NDVI timeline response"""
    field_id: int
    start_date: date
    end_date: date
    data: List[NDVIResponse]
    trend: Optional[str]  # improving, declining, stable


class NDVIComputeRequest(BaseModel):
    """Request to compute NDVI"""
    field_ids: List[int]
    start_date: date
    end_date: date
    force_recompute: bool = False


class NDVIComputeResponse(BaseModel):
    """Response for NDVI computation request"""
    job_id: str
    status: str
    field_count: int
    estimated_time_seconds: Optional[int]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Schemas - Advisor
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/schemas/advisor.py" << 'EOF'
"""
Advisor Schemas
مخططات المستشار
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class AlertType(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


# ─────────────────────────────────────────────────────────────────────────────
# Context Schemas
# ─────────────────────────────────────────────────────────────────────────────
class NDVIContext(BaseModel):
    """NDVI context for analysis"""
    mean: float
    min: float
    max: float
    std: float
    zones: Dict[str, float]
    trend: Optional[str] = None


class WeatherContext(BaseModel):
    """Weather context for analysis"""
    temperature_max: float
    temperature_min: float
    temperature_mean: float
    humidity: float
    precipitation_mm: float
    wind_speed: float
    forecast: Optional[List[Dict]] = None


class CropContext(BaseModel):
    """Crop context for analysis"""
    crop_type: str
    growth_stage: Optional[str] = None
    days_since_planting: Optional[int] = None
    expected_harvest_days: Optional[int] = None


class SoilContext(BaseModel):
    """Soil context for analysis"""
    moisture: Optional[float] = None
    ph: Optional[float] = None
    nitrogen: Optional[str] = None
    phosphorus: Optional[str] = None
    potassium: Optional[str] = None


class FieldContext(BaseModel):
    """Complete field context for advisor"""
    field_id: int
    field_name: str
    tenant_id: int
    ndvi: Optional[NDVIContext] = None
    weather: Optional[WeatherContext] = None
    crop: Optional[CropContext] = None
    soil: Optional[SoilContext] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Action Schemas
# ─────────────────────────────────────────────────────────────────────────────
class ActionItem(BaseModel):
    """Action item in recommendation"""
    action_ar: str
    action_en: str
    urgency: str  # immediate, within_24h, within_48h, routine
    estimated_duration: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────────────
class AdvisorAnalyzeRequest(BaseModel):
    """Request to analyze a field"""
    field_id: int
    include_weather: bool = True
    include_forecast: bool = True


class RecommendationResponse(BaseModel):
    """Recommendation response"""
    id: int
    uuid: str
    rule_name: str
    category: str
    priority: RecommendationPriority
    status: RecommendationStatus
    title_ar: str
    title_en: str
    description_ar: Optional[str]
    description_en: Optional[str]
    actions: List[ActionItem]
    confidence_score: float
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    """Alert response"""
    id: int
    uuid: str
    alert_type: AlertType
    category: str
    title: str
    message: Optional[str]
    is_read: bool
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdvisorSessionResponse(BaseModel):
    """Advisor session response"""
    id: int
    uuid: str
    field_id: int
    session_type: str
    health_score: Optional[float]
    risk_score: Optional[float]
    recommendations: List[RecommendationResponse]
    alerts: List[AlertResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationAction(BaseModel):
    """Action on a recommendation"""
    action: str  # accept, reject, complete, defer
    notes: Optional[str] = None
EOF

log_success "تم إنشاء نماذج قاعدة البيانات"

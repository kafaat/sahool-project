#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 4: Backend Services - Field, NDVI, Advisor
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء خدمات الأعمال..."

# ─────────────────────────────────────────────────────────────────────────────
# Field Service
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/services/field_service.py" << 'EOF'
"""
Field Service
خدمة الحقول
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_Area, ST_Centroid, ST_X, ST_Y, ST_Transform
from shapely import wkt
from shapely.geometry import shape
import json

from app.models.field import Field
from app.schemas.field import FieldCreate, FieldUpdate, FieldResponse
from app.core.redis import RedisManager
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldService:
    """Service for field operations"""

    CACHE_PREFIX = "field"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, db: AsyncSession, redis: RedisManager):
        self.db = db
        self.redis = redis

    async def get_fields(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 20,
        crop_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Field], int]:
        """Get paginated list of fields for tenant"""
        # Build query
        query = select(Field).where(Field.tenant_id == tenant_id)

        if crop_type:
            query = query.where(Field.crop_type == crop_type)
        if status:
            query = query.where(Field.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply pagination
        query = query.order_by(Field.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        fields = result.scalars().all()

        return fields, total

    async def get_field(self, field_id: int, tenant_id: int) -> Optional[Field]:
        """Get single field by ID"""
        # Check cache first
        cache_key = f"{self.CACHE_PREFIX}:{tenant_id}:{field_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for field {field_id}")
            # Note: returning cached dict, need to handle in API
            return cached

        result = await self.db.execute(
            select(Field).where(
                Field.id == field_id,
                Field.tenant_id == tenant_id
            )
        )
        field = result.scalar_one_or_none()

        if field:
            # Cache the result
            await self.redis.set(cache_key, self._field_to_dict(field), self.CACHE_TTL)

        return field

    async def create_field(self, field_data: FieldCreate, tenant_id: int, owner_id: int) -> Field:
        """Create a new field"""
        # Validate geometry
        try:
            geom = shape(field_data.geometry)
            if not geom.is_valid:
                raise ValidationError("Invalid geometry")
            geom_wkt = geom.wkt
        except Exception as e:
            raise ValidationError(f"Invalid GeoJSON geometry: {str(e)}")

        # Create field
        field = Field(
            tenant_id=tenant_id,
            owner_id=owner_id,
            name=field_data.name,
            description=field_data.description,
            crop_type=field_data.crop_type,
            crop_variety=field_data.crop_variety,
            geometry=f"SRID=4326;{geom_wkt}",
            planting_date=field_data.planting_date,
            expected_harvest_date=field_data.expected_harvest_date,
            metadata=field_data.metadata
        )

        self.db.add(field)
        await self.db.flush()

        # Calculate area and centroid using PostGIS
        await self._update_field_geometry_info(field.id)

        await self.db.commit()
        await self.db.refresh(field)

        logger.info(f"Created field: {field.id} for tenant {tenant_id}")

        # Invalidate cache
        await self.redis.delete_pattern(f"{self.CACHE_PREFIX}:{tenant_id}:*")

        return field

    async def update_field(
        self,
        field_id: int,
        tenant_id: int,
        update_data: FieldUpdate
    ) -> Field:
        """Update a field"""
        field = await self.get_field(field_id, tenant_id)
        if not field:
            raise NotFoundError("Field", field_id)

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(field, key, value)

        await self.db.commit()
        await self.db.refresh(field)

        # Invalidate cache
        await self.redis.delete(f"{self.CACHE_PREFIX}:{tenant_id}:{field_id}")

        logger.info(f"Updated field: {field_id}")
        return field

    async def delete_field(self, field_id: int, tenant_id: int) -> bool:
        """Delete a field"""
        field = await self.get_field(field_id, tenant_id)
        if not field:
            raise NotFoundError("Field", field_id)

        await self.db.execute(
            delete(Field).where(Field.id == field_id)
        )
        await self.db.commit()

        # Invalidate cache
        await self.redis.delete(f"{self.CACHE_PREFIX}:{tenant_id}:{field_id}")
        await self.redis.delete_pattern(f"{self.CACHE_PREFIX}:{tenant_id}:*")

        logger.info(f"Deleted field: {field_id}")
        return True

    async def _update_field_geometry_info(self, field_id: int) -> None:
        """Update area and centroid for a field"""
        # Calculate area in hectares (transform to UTM for accurate area)
        area_query = select(
            ST_Area(ST_Transform(Field.geometry, 32637)) / 10000  # Square meters to hectares
        ).where(Field.id == field_id)
        area = await self.db.scalar(area_query)

        # Calculate centroid
        centroid_query = select(
            ST_X(ST_Centroid(Field.geometry)),
            ST_Y(ST_Centroid(Field.geometry))
        ).where(Field.id == field_id)
        result = await self.db.execute(centroid_query)
        lon, lat = result.first()

        # Update field
        await self.db.execute(
            update(Field).where(Field.id == field_id).values(
                area_ha=area,
                centroid_lat=lat,
                centroid_lon=lon
            )
        )

    def _field_to_dict(self, field: Field) -> dict:
        """Convert field to dictionary for caching"""
        return {
            "id": field.id,
            "uuid": field.uuid,
            "tenant_id": field.tenant_id,
            "name": field.name,
            "description": field.description,
            "crop_type": field.crop_type,
            "area_ha": field.area_ha,
            "status": field.status,
            "created_at": field.created_at.isoformat() if field.created_at else None
        }
EOF

# ─────────────────────────────────────────────────────────────────────────────
# NDVI Service
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/services/ndvi_service.py" << 'EOF'
"""
NDVI Service
خدمة تحليل NDVI
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import numpy as np

from app.models.ndvi import NDVIResult
from app.models.field import Field
from app.schemas.ndvi import NDVIResponse, NDVITimelineResponse, NDVIComputeRequest
from app.core.redis import RedisManager
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.tasks.ndvi_tasks import compute_ndvi_task

logger = get_logger(__name__)


class NDVIService:
    """Service for NDVI analysis operations"""

    CACHE_PREFIX = "ndvi"
    CACHE_TTL = 1800  # 30 minutes

    def __init__(self, db: AsyncSession, redis: RedisManager):
        self.db = db
        self.redis = redis

    async def get_latest_ndvi(
        self,
        field_id: int,
        tenant_id: int
    ) -> Optional[NDVIResult]:
        """Get latest NDVI result for a field"""
        # Check cache
        cache_key = f"{self.CACHE_PREFIX}:latest:{field_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(NDVIResult)
            .where(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id
            )
            .order_by(NDVIResult.analysis_date.desc())
            .limit(1)
        )
        ndvi = result.scalar_one_or_none()

        if ndvi:
            await self.redis.set(cache_key, self._ndvi_to_dict(ndvi), self.CACHE_TTL)

        return ndvi

    async def get_ndvi_by_date(
        self,
        field_id: int,
        tenant_id: int,
        target_date: date
    ) -> Optional[NDVIResult]:
        """Get NDVI result for specific date"""
        cache_key = f"{self.CACHE_PREFIX}:{field_id}:{target_date}"
        cached = await self.redis.get(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(NDVIResult)
            .where(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
                NDVIResult.analysis_date == target_date
            )
        )
        ndvi = result.scalar_one_or_none()

        if ndvi:
            await self.redis.set(cache_key, self._ndvi_to_dict(ndvi), self.CACHE_TTL)

        return ndvi

    async def get_ndvi_timeline(
        self,
        field_id: int,
        tenant_id: int,
        start_date: date,
        end_date: date
    ) -> List[NDVIResult]:
        """Get NDVI timeline for a field"""
        # Validate date range
        if start_date > end_date:
            raise ValidationError("Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise ValidationError("Date range cannot exceed 1 year")

        result = await self.db.execute(
            select(NDVIResult)
            .where(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
                NDVIResult.analysis_date.between(start_date, end_date)
            )
            .order_by(NDVIResult.analysis_date.asc())
        )

        return result.scalars().all()

    async def get_ndvi_statistics(
        self,
        field_id: int,
        tenant_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get NDVI statistics for a field"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        timeline = await self.get_ndvi_timeline(field_id, tenant_id, start_date, end_date)

        if not timeline:
            return {
                "field_id": field_id,
                "period_days": days,
                "data_points": 0,
                "statistics": None,
                "trend": None
            }

        values = [r.mean_ndvi for r in timeline]

        # Calculate trend
        if len(values) >= 2:
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            if slope > 0.01:
                trend = "improving"
            elif slope < -0.01:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "field_id": field_id,
            "period_days": days,
            "data_points": len(values),
            "statistics": {
                "mean": float(np.mean(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "std": float(np.std(values)),
                "latest": values[-1] if values else None
            },
            "trend": trend
        }

    async def trigger_computation(
        self,
        request: NDVIComputeRequest,
        tenant_id: int
    ) -> str:
        """Trigger NDVI computation for fields"""
        # Validate fields exist and belong to tenant
        for field_id in request.field_ids:
            result = await self.db.execute(
                select(Field).where(
                    Field.id == field_id,
                    Field.tenant_id == tenant_id
                )
            )
            if not result.scalar_one_or_none():
                raise NotFoundError("Field", field_id)

        # Queue the task
        task = compute_ndvi_task.delay(
            field_ids=request.field_ids,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            tenant_id=tenant_id,
            force_recompute=request.force_recompute
        )

        logger.info(f"Queued NDVI computation task: {task.id}")
        return task.id

    async def save_ndvi_result(
        self,
        field_id: int,
        tenant_id: int,
        analysis_date: date,
        ndvi_data: Dict[str, Any]
    ) -> NDVIResult:
        """Save NDVI analysis result"""
        # Check if result already exists
        existing = await self.get_ndvi_by_date(field_id, tenant_id, analysis_date)
        if existing:
            # Update existing
            for key, value in ndvi_data.items():
                setattr(existing, key, value)
            await self.db.commit()
            return existing

        # Create new
        result = NDVIResult(
            field_id=field_id,
            tenant_id=tenant_id,
            analysis_date=analysis_date,
            **ndvi_data
        )

        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        # Invalidate cache
        await self.redis.delete(f"{self.CACHE_PREFIX}:latest:{field_id}")

        logger.info(f"Saved NDVI result for field {field_id} date {analysis_date}")
        return result

    def _ndvi_to_dict(self, ndvi: NDVIResult) -> dict:
        """Convert NDVI result to dictionary"""
        return {
            "id": ndvi.id,
            "field_id": ndvi.field_id,
            "analysis_date": ndvi.analysis_date.isoformat(),
            "mean_ndvi": ndvi.mean_ndvi,
            "min_ndvi": ndvi.min_ndvi,
            "max_ndvi": ndvi.max_ndvi,
            "std_ndvi": ndvi.std_ndvi,
            "zones": ndvi.zones,
            "tile_url": ndvi.tile_url
        }
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Advisor Service
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/services/advisor_service.py" << 'EOF'
"""
Advisor Service
خدمة المستشار الزراعي
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import yaml
from pathlib import Path

from app.models.advisor import (
    AdvisorSession, Recommendation, Alert,
    RecommendationPriority, RecommendationStatus, AlertType
)
from app.models.field import Field
from app.schemas.advisor import (
    FieldContext, NDVIContext, WeatherContext, CropContext,
    AdvisorAnalyzeRequest, AdvisorSessionResponse, RecommendationAction
)
from app.core.redis import RedisManager
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.services.ndvi_service import NDVIService

logger = get_logger(__name__)


class AdvisorService:
    """Smart agricultural advisor service"""

    def __init__(self, db: AsyncSession, redis: RedisManager):
        self.db = db
        self.redis = redis
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict]:
        """Load advisor rules"""
        # Default rules (can be loaded from YAML files)
        return [
            {
                "name": "critical_low_ndvi",
                "category": "irrigation",
                "priority": "critical",
                "conditions": [
                    {"field": "ndvi.mean", "operator": "<", "value": 0.2}
                ],
                "recommendation": {
                    "title_ar": "تحذير: صحة نباتية حرجة",
                    "title_en": "Critical: Very Low Plant Health",
                    "description_ar": "مؤشر NDVI منخفض جداً (<0.2) - يدل على إجهاد شديد أو موت النباتات",
                    "description_en": "NDVI is critically low (<0.2) - indicates severe stress or plant death",
                    "actions": [
                        {"action_ar": "فحص ميداني فوري", "action_en": "Immediate field inspection", "urgency": "immediate"},
                        {"action_ar": "فحص نظام الري", "action_en": "Check irrigation system", "urgency": "immediate"},
                        {"action_ar": "فحص التربة للأمراض", "action_en": "Check soil for diseases", "urgency": "within_24h"}
                    ]
                }
            },
            {
                "name": "low_ndvi_irrigation",
                "category": "irrigation",
                "priority": "high",
                "conditions": [
                    {"field": "ndvi.mean", "operator": "<", "value": 0.4},
                    {"field": "ndvi.mean", "operator": ">=", "value": 0.2}
                ],
                "recommendation": {
                    "title_ar": "زيادة الري المطلوبة",
                    "title_en": "Increased Irrigation Required",
                    "description_ar": "مؤشر النبات منخفض - يُنصح بزيادة كمية الري",
                    "description_en": "Plant index is low - increasing irrigation is recommended",
                    "actions": [
                        {"action_ar": "زيادة الري بنسبة 20%", "action_en": "Increase irrigation by 20%", "urgency": "within_24h"},
                        {"action_ar": "مراقبة رطوبة التربة", "action_en": "Monitor soil moisture", "urgency": "routine"}
                    ]
                }
            },
            {
                "name": "high_temp_stress",
                "category": "weather",
                "priority": "critical",
                "conditions": [
                    {"field": "weather.temperature_max", "operator": ">", "value": 40}
                ],
                "recommendation": {
                    "title_ar": "إجهاد حراري شديد",
                    "title_en": "Severe Heat Stress",
                    "description_ar": "درجة الحرارة تجاوزت 40°م - خطر إجهاد حراري على المحصول",
                    "description_en": "Temperature exceeded 40°C - crop heat stress risk",
                    "actions": [
                        {"action_ar": "الري في الصباح الباكر فقط", "action_en": "Irrigate early morning only", "urgency": "immediate"},
                        {"action_ar": "تظليل النباتات الحساسة", "action_en": "Shade sensitive plants", "urgency": "within_24h"},
                        {"action_ar": "زيادة تردد الري", "action_en": "Increase irrigation frequency", "urgency": "within_24h"}
                    ]
                }
            },
            {
                "name": "ndvi_variability",
                "category": "fertilization",
                "priority": "medium",
                "conditions": [
                    {"field": "ndvi.std", "operator": ">", "value": 0.15}
                ],
                "recommendation": {
                    "title_ar": "تباين في صحة النباتات",
                    "title_en": "Plant Health Variability",
                    "description_ar": "تباين كبير في صحة النباتات داخل الحقل - قد يدل على مشاكل في التغذية",
                    "description_en": "High variability in plant health within field - may indicate nutrient issues",
                    "actions": [
                        {"action_ar": "تحليل عينات التربة", "action_en": "Soil sample analysis", "urgency": "within_48h"},
                        {"action_ar": "تسميد متغير المعدل", "action_en": "Variable rate fertilization", "urgency": "routine"}
                    ]
                }
            },
            {
                "name": "optimal_harvest",
                "category": "harvest",
                "priority": "medium",
                "conditions": [
                    {"field": "ndvi.mean", "operator": ">=", "value": 0.7},
                    {"field": "crop.growth_stage", "operator": "==", "value": "maturity"}
                ],
                "recommendation": {
                    "title_ar": "موعد الحصاد الأمثل",
                    "title_en": "Optimal Harvest Time",
                    "description_ar": "المحصول في مرحلة النضج والصحة النباتية ممتازة - الوقت مناسب للحصاد",
                    "description_en": "Crop is at maturity stage with excellent health - optimal time for harvest",
                    "actions": [
                        {"action_ar": "تجهيز معدات الحصاد", "action_en": "Prepare harvesting equipment", "urgency": "within_48h"},
                        {"action_ar": "التنسيق مع فريق الحصاد", "action_en": "Coordinate with harvest team", "urgency": "routine"}
                    ]
                }
            }
        ]

    async def analyze_field(
        self,
        request: AdvisorAnalyzeRequest,
        tenant_id: int
    ) -> AdvisorSession:
        """Analyze a field and generate recommendations"""
        # Get field
        result = await self.db.execute(
            select(Field).where(
                Field.id == request.field_id,
                Field.tenant_id == tenant_id
            )
        )
        field = result.scalar_one_or_none()
        if not field:
            raise NotFoundError("Field", request.field_id)

        # Build context
        context = await self._build_context(field, request)

        # Create session
        session = AdvisorSession(
            field_id=field.id,
            tenant_id=tenant_id,
            session_type="full_analysis",
            ndvi_context=context.ndvi.model_dump() if context.ndvi else None,
            weather_context=context.weather.model_dump() if context.weather else None,
            crop_context=context.crop.model_dump() if context.crop else None
        )
        self.db.add(session)
        await self.db.flush()

        # Evaluate rules and generate recommendations
        recommendations = []
        alerts = []

        for rule in self.rules:
            if self._evaluate_conditions(rule["conditions"], context):
                rec_data = rule["recommendation"]

                rec = Recommendation(
                    session_id=session.id,
                    field_id=field.id,
                    tenant_id=tenant_id,
                    rule_name=rule["name"],
                    category=rule["category"],
                    priority=RecommendationPriority(rule["priority"]),
                    title_ar=rec_data["title_ar"],
                    title_en=rec_data["title_en"],
                    description_ar=rec_data.get("description_ar"),
                    description_en=rec_data.get("description_en"),
                    actions=rec_data.get("actions", []),
                    confidence_score=0.85,
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                recommendations.append(rec)

                # Create alert for critical/high priority
                if rule["priority"] in ["critical", "high"]:
                    alert = Alert(
                        session_id=session.id,
                        field_id=field.id,
                        tenant_id=tenant_id,
                        alert_type=AlertType.CRITICAL if rule["priority"] == "critical" else AlertType.WARNING,
                        category=rule["category"],
                        title=rec_data["title_ar"],
                        message=rec_data.get("description_ar")
                    )
                    alerts.append(alert)

        # Add recommendations and alerts
        for rec in recommendations:
            self.db.add(rec)
        for alert in alerts:
            self.db.add(alert)

        # Calculate scores
        session.health_score = self._calculate_health_score(context)
        session.risk_score = self._calculate_risk_score(recommendations)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Analyzed field {field.id}: {len(recommendations)} recommendations, {len(alerts)} alerts")

        return session

    async def _build_context(
        self,
        field: Field,
        request: AdvisorAnalyzeRequest
    ) -> FieldContext:
        """Build field context for analysis"""
        # Get latest NDVI
        ndvi_service = NDVIService(self.db, self.redis)
        latest_ndvi = await ndvi_service.get_latest_ndvi(field.id, field.tenant_id)

        ndvi_context = None
        if latest_ndvi:
            ndvi_context = NDVIContext(
                mean=latest_ndvi.mean_ndvi,
                min=latest_ndvi.min_ndvi or 0,
                max=latest_ndvi.max_ndvi or 1,
                std=latest_ndvi.std_ndvi or 0,
                zones=latest_ndvi.zones or {}
            )

        # Get weather (mock for now)
        weather_context = WeatherContext(
            temperature_max=35,
            temperature_min=22,
            temperature_mean=28,
            humidity=45,
            precipitation_mm=0,
            wind_speed=12
        )

        # Get crop context
        crop_context = CropContext(
            crop_type=field.crop_type or "unknown",
            growth_stage="vegetative"
        )
        if field.planting_date:
            days = (datetime.utcnow().date() - field.planting_date.date()).days
            crop_context.days_since_planting = days

        return FieldContext(
            field_id=field.id,
            field_name=field.name,
            tenant_id=field.tenant_id,
            ndvi=ndvi_context,
            weather=weather_context,
            crop=crop_context
        )

    def _evaluate_conditions(
        self,
        conditions: List[Dict],
        context: FieldContext
    ) -> bool:
        """Evaluate rule conditions against context"""
        for condition in conditions:
            field_path = condition["field"].split(".")
            value = context

            # Navigate to the field
            for path in field_path:
                if hasattr(value, path):
                    value = getattr(value, path)
                elif isinstance(value, dict) and path in value:
                    value = value[path]
                else:
                    return False

            if value is None:
                return False

            # Evaluate condition
            op = condition["operator"]
            target = condition["value"]

            if op == "<" and not (value < target):
                return False
            elif op == ">" and not (value > target):
                return False
            elif op == "<=" and not (value <= target):
                return False
            elif op == ">=" and not (value >= target):
                return False
            elif op == "==" and not (value == target):
                return False
            elif op == "!=" and not (value != target):
                return False

        return True

    def _calculate_health_score(self, context: FieldContext) -> float:
        """Calculate overall health score (0-100)"""
        scores = []

        # NDVI score
        if context.ndvi:
            ndvi_score = min(context.ndvi.mean * 100, 100)
            scores.append(ndvi_score)

        # Weather score
        if context.weather:
            temp = context.weather.temperature_mean
            if 20 <= temp <= 30:
                weather_score = 100
            elif 15 <= temp <= 35:
                weather_score = 70
            else:
                weather_score = 40
            scores.append(weather_score)

        return sum(scores) / len(scores) if scores else 50

    def _calculate_risk_score(self, recommendations: List[Recommendation]) -> float:
        """Calculate risk score based on recommendations"""
        if not recommendations:
            return 0

        priority_scores = {
            RecommendationPriority.CRITICAL: 100,
            RecommendationPriority.HIGH: 70,
            RecommendationPriority.MEDIUM: 40,
            RecommendationPriority.LOW: 20
        }

        max_score = max(priority_scores.get(r.priority, 0) for r in recommendations)
        return max_score

    async def get_session(
        self,
        session_id: int,
        tenant_id: int
    ) -> Optional[AdvisorSession]:
        """Get advisor session by ID"""
        result = await self.db.execute(
            select(AdvisorSession)
            .where(
                AdvisorSession.id == session_id,
                AdvisorSession.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def update_recommendation_status(
        self,
        recommendation_id: int,
        tenant_id: int,
        action: RecommendationAction
    ) -> Recommendation:
        """Update recommendation status"""
        result = await self.db.execute(
            select(Recommendation).where(
                Recommendation.id == recommendation_id,
                Recommendation.tenant_id == tenant_id
            )
        )
        rec = result.scalar_one_or_none()
        if not rec:
            raise NotFoundError("Recommendation", recommendation_id)

        status_map = {
            "accept": RecommendationStatus.ACCEPTED,
            "reject": RecommendationStatus.REJECTED,
            "complete": RecommendationStatus.COMPLETED
        }

        rec.status = status_map.get(action.action, rec.status)
        if action.action == "complete":
            rec.completed_at = datetime.utcnow()

        await self.db.commit()
        return rec
EOF

log_success "تم إنشاء خدمات الأعمال"

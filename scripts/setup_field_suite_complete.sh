#!/bin/bash
set -e

# =====================================
# 🌾 Field Suite Complete Project Generator
# =====================================
# هذا السكربت ينشئ مشروع Field Suite كاملاً
# يتضمن: Backend + Frontend + Docker + Services
# =====================================

# ألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_NAME="${1:-field_suite_complete}"

echo -e "${GREEN}🌾 إنشاء مشروع Field Suite الكامل${NC}"
echo -e "${BLUE}اسم المشروع: $PROJECT_NAME${NC}"

# دالة كتابة الملفات
write_file() {
    local file_path="$1"
    local content="$2"
    mkdir -p "$(dirname "$file_path")"
    echo "$content" > "$file_path"
    echo -e "${GREEN}✅ تم إنشاء: $file_path${NC}"
}

# =====================================
# إنشاء هيكل المجلدات
# =====================================
echo -e "${BLUE}📁 إنشاء هيكل المجلدات...${NC}"

mkdir -p "$PROJECT_NAME"/{backend/app/{api/v1,core,models,schemas,services,repositories,tasks},web/src/{api,components/{advisor,fields,ndvi,common},hooks,pages,types,utils},scripts,tests/{unit,integration,e2e},docs,infra/{docker,k8s}}

# =====================================
# 10️⃣ إنشاء ملفات الباكند الأساسية (الإكمال)
# =====================================
echo -e "${BLUE}🐍 إنشاء ملفات الباكند الأساسية...${NC}"

# Core Config
write_file "$PROJECT_NAME/backend/app/core/config.py" 'from pydantic import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "field_suite_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # APIs
    OPENWEATHER_API_KEY: str = ""
    SENTINEL_CLIENT_ID: str = ""
    SENTINEL_CLIENT_SECRET: str = ""

    # Features
    ENABLE_ADVISOR: bool = True
    ENABLE_NDVI_CACHE: bool = True
    ENABLE_RATE_LIMITING: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()'

# Logging Config
write_file "$PROJECT_NAME/backend/app/core/logging_config.py" 'import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

def setup_logging():
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_obj: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # إضافة extra fields إذا وجدت
            if hasattr(record, "extra"):
                log_obj.update(record.extra)

            # إضافة exception info
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_obj)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)'

# API Router - fields
write_file "$PROJECT_NAME/backend/app/api/v1/fields.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.field import FieldResponse, FieldCreate
from app.services.field_service import FieldService
from app.dependencies import get_field_service, get_current_user

router = APIRouter()

@router.get("/fields", response_model=List[FieldResponse])
async def get_fields(
    skip: int = 0,
    limit: int = 100,
    field_service: FieldService = Depends(get_field_service),
    current_user=Depends(get_current_user)
):
    fields = await field_service.get_fields(current_user.tenant_id, skip, limit)
    return fields

@router.post("/fields", response_model=FieldResponse)
async def create_field(
    field: FieldCreate,
    field_service: FieldService = Depends(get_field_service),
    current_user=Depends(get_current_user)
):
    return await field_service.create_field(field, current_user.tenant_id)

@router.get("/fields/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: int,
    field_service: FieldService = Depends(get_field_service),
    current_user=Depends(get_current_user)
):
    field = await field_service.get_field(field_id, current_user.tenant_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field'

# API Router - ndvi
write_file "$PROJECT_NAME/backend/app/api/v1/ndvi.py" 'from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from datetime import date
from app.schemas.ndvi import NDVIResponse, NDVITimelineResponse, NDVIComputeRequest
from app.services.ndvi_service import NDVIService
from app.dependencies import get_ndvi_service, get_current_user, limiter

router = APIRouter()

@router.get("/ndvi/{field_id}", response_model=NDVIResponse)
@limiter.limit("100/minute")
async def get_ndvi(
    request: Request,
    field_id: int,
    target_date: Optional[date] = Query(None),
    ndvi_service: NDVIService = Depends(get_ndvi_service),
    current_user=Depends(get_current_user)
):
    result = await ndvi_service.get_ndvi(field_id, target_date, current_user.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="NDVI data not found")
    return result

@router.post("/ndvi/compute", status_code=202)
@limiter.limit("10/minute")
async def trigger_ndvi_computation(
    request: Request,
    compute_request: NDVIComputeRequest,
    ndvi_service: NDVIService = Depends(get_ndvi_service),
    current_user=Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    job_id = await ndvi_service.trigger_computation(
        compute_request.field_ids,
        compute_request.date_range,
        current_user.tenant_id
    )
    return {"job_id": job_id, "status": "queued"}

@router.get("/ndvi/{field_id}/timeline", response_model=NDVITimelineResponse)
@limiter.limit("100/minute")
async def get_ndvi_timeline(
    request: Request,
    field_id: int,
    start_date: date,
    end_date: date,
    ndvi_service: NDVIService = Depends(get_ndvi_service),
    current_user=Depends(get_current_user)
):
    timeline = await ndvi_service.get_timeline(
        field_id, start_date, end_date, current_user.tenant_id
    )
    return {"field_id": field_id, "data": timeline}

@router.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy", "service": "ndvi-api"}'

# API Router - advisor
write_file "$PROJECT_NAME/backend/app/api/v1/advisor.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.advisor import FieldContext, Recommendation, AdvisorRequest
from app.services.advisor_service import AdvisorService
from app.dependencies import get_advisor_service, get_current_user

router = APIRouter()

@router.post("/advisor/analyze-field", response_model=List[Recommendation])
async def analyze_field(
    request: AdvisorRequest,
    advisor_service: AdvisorService = Depends(get_advisor_service),
    current_user=Depends(get_current_user)
):
    context = await advisor_service.build_context(request.field_id, current_user.tenant_id)
    recommendations = await advisor_service.analyze(context)
    return recommendations

@router.get("/advisor/fields/{field_id}/history", response_model=List[Recommendation])
async def get_advisor_history(
    field_id: int,
    advisor_service: AdvisorService = Depends(get_advisor_service),
    current_user=Depends(get_current_user)
):
    history = await advisor_service.get_history(field_id, current_user.tenant_id)
    return history

@router.get("/advisor/rules", response_model=List[str])
async def get_available_rules(
    advisor_service: AdvisorService = Depends(get_advisor_service),
    current_user=Depends(get_current_user)
):
    return advisor_service.get_available_rules()'

# Schemas - field
write_file "$PROJECT_NAME/backend/app/schemas/field.py" 'from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class FieldCreate(BaseModel):
    name: str
    crop_type: str
    geometry: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class FieldResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    crop_type: str
    geometry: Dict[str, Any]
    area_ha: Optional[float]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True'

# Schemas - ndvi
write_file "$PROJECT_NAME/backend/app/schemas/ndvi.py" 'from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

class NDVIZones(BaseModel):
    low: Dict[str, float]
    medium: Dict[str, float]
    high: Dict[str, float]

class NDVIResponse(BaseModel):
    field_id: int
    date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    std_ndvi: float
    pixel_count: int
    zones: NDVIZones
    tile_url: Optional[str] = None

class NDVITimelineResponse(BaseModel):
    field_id: int
    data: List[NDVIResponse]

class NDVIComputeRequest(BaseModel):
    field_ids: List[int]
    date_range: Dict[str, date]'

# Schemas - advisor
write_file "$PROJECT_NAME/backend/app/schemas/advisor.py" 'from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class NDVIContext(BaseModel):
    mean: float
    min: float
    max: float
    zones: Dict[str, float]

class WeatherContext(BaseModel):
    tmax: float
    tmin: float
    tmean: float
    rain_mm: float
    humidity: float
    wind_speed: float

class CropContext(BaseModel):
    type: str
    growth_stage: Optional[str] = None
    planting_date: Optional[str] = None

class FieldContext(BaseModel):
    field_id: int
    tenant_id: int
    name: str
    ndvi: NDVIContext
    weather: WeatherContext
    crop: CropContext
    timestamp: datetime = datetime.utcnow()

class RecommendationAction(BaseModel):
    action_ar: str
    action_en: str
    urgency: str

class Recommendation(BaseModel):
    id: str
    rule_name: str
    priority: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[RecommendationAction]
    field_id: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AdvisorRequest(BaseModel):
    field_id: int

class Rule(BaseModel):
    name: str
    category: str
    conditions: List[Dict[str, Any]]
    recommendation: Dict[str, Any]'

# Services - field
write_file "$PROJECT_NAME/backend/app/services/field_service.py" 'from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.field import Field
from app.schemas.field import FieldCreate

class FieldService:
    def __init__(self, db: Session):
        self.db = db

    async def get_fields(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Field]:
        return self.db.query(Field).filter(Field.tenant_id == tenant_id).offset(skip).limit(limit).all()

    async def create_field(self, field_data: FieldCreate, tenant_id: int) -> Field:
        field = Field(**field_data.dict(), tenant_id=tenant_id)
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    async def get_field(self, field_id: int, tenant_id: int) -> Optional[Field]:
        return self.db.query(Field).filter(
            Field.id == field_id,
            Field.tenant_id == tenant_id
        ).first()'

# Services - ndvi
write_file "$PROJECT_NAME/backend/app/services/ndvi_service.py" 'from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date
import redis
import json
from celery import Celery
from app.models.ndvi import NDVIResult
from app.repositories.ndvi_repository import NDVIRepository
from app.repositories.field_repository import FieldRepository

class NDVIService:
    def __init__(self, db: Session, cache: redis.Redis):
        self.db = db
        self.cache = cache
        self.ndvi_repo = NDVIRepository(db)
        self.field_repo = FieldRepository(db)
        self.celery_app = Celery("ndvi_tasks", broker="redis://redis:6379", backend="redis://redis:6379")

    async def get_ndvi(self, field_id: int, target_date: Optional[date] = None, tenant_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        cache_key = f"ndvi:{field_id}:{target_date or '\''latest'\''}"

        cached_data = self.cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        result = await self.ndvi_repo.get_ndvi(field_id, target_date)

        if result and tenant_id:
            field = await self.field_repo.get_field(field_id, tenant_id)
            if not field:
                return None

        if result:
            self.cache.setex(cache_key, 3600, json.dumps(result))

        return result

    async def trigger_computation(self, field_ids: List[int], date_range: Dict[str, date], tenant_id: int) -> str:
        for field_id in field_ids:
            field = await self.field_repo.get_field(field_id, tenant_id)
            if not field:
                raise ValueError(f"Field {field_id} not found or not owned by tenant")

        task = self.celery_app.send_task("tasks.compute_ndvi_batch", args=[field_ids, date_range, tenant_id], queue="ndvi")
        return task.id

    async def get_timeline(self, field_id: int, start_date: date, end_date: date, tenant_id: int) -> List[Dict[str, Any]]:
        cache_key = f"timeline:{field_id}:{start_date}:{end_date}"

        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        results = await self.ndvi_repo.get_timeline(field_id, start_date, end_date)

        field = await self.field_repo.get_field(field_id, tenant_id)
        if not field:
            return []

        self.cache.setex(cache_key, 1800, json.dumps(results))

        return results'

# Services - advisor
write_file "$PROJECT_NAME/backend/app/services/advisor_service.py" 'from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import redis
import json
import uuid
from app.schemas.advisor import FieldContext, Recommendation, NDVIContext, WeatherContext, CropContext
from app.repositories.field_repository import FieldRepository
from app.repositories.ndvi_repository import NDVIRepository

class AdvisorService:
    def __init__(self, db: Session, cache: redis.Redis):
        self.db = db
        self.cache = cache
        self.field_repo = FieldRepository(db)
        self.ndvi_repo = NDVIRepository(db)
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict]:
        """تحميل قواعد التوصيات"""
        return [
            {
                "name": "low_ndvi_irrigation",
                "category": "irrigation",
                "conditions": [{"field": "ndvi.mean", "operator": "<", "value": 0.4}],
                "priority": "high",
                "recommendation": {
                    "title_ar": "زيادة الري",
                    "title_en": "Increase Irrigation",
                    "description_ar": "مؤشر صحة النبات منخفض - يُنصح بزيادة كمية الري",
                    "description_en": "Plant health index is low - increase irrigation recommended",
                    "actions": [
                        {"action_ar": "زيادة الري بنسبة 20%", "action_en": "Increase irrigation by 20%", "urgency": "within_24h"},
                        {"action_ar": "فحص نظام الري", "action_en": "Check irrigation system", "urgency": "routine"}
                    ]
                }
            },
            {
                "name": "high_temp_stress",
                "category": "weather",
                "conditions": [{"field": "weather.tmax", "operator": ">", "value": 38}],
                "priority": "critical",
                "recommendation": {
                    "title_ar": "إجهاد حراري",
                    "title_en": "Heat Stress Alert",
                    "description_ar": "درجة الحرارة مرتفعة جداً - خطر إجهاد حراري على المحصول",
                    "description_en": "Temperature is very high - crop heat stress risk",
                    "actions": [
                        {"action_ar": "الري في الصباح الباكر", "action_en": "Irrigate early morning", "urgency": "immediate"},
                        {"action_ar": "تظليل النباتات الحساسة", "action_en": "Shade sensitive plants", "urgency": "within_24h"}
                    ]
                }
            },
            {
                "name": "ndvi_variability",
                "category": "fertilization",
                "conditions": [{"field": "ndvi.zones.low", "operator": ">", "value": 0.3}],
                "priority": "medium",
                "recommendation": {
                    "title_ar": "تباين في صحة النباتات",
                    "title_en": "Vegetation Variability",
                    "description_ar": "يوجد تباين كبير في صحة النباتات - قد يدل على نقص تغذية",
                    "description_en": "High variability in plant health - may indicate nutrient deficiency",
                    "actions": [
                        {"action_ar": "فحص التربة", "action_en": "Soil testing", "urgency": "within_48h"},
                        {"action_ar": "تسميد متغير المعدل", "action_en": "Variable rate fertilization", "urgency": "routine"}
                    ]
                }
            }
        ]

    async def build_context(self, field_id: int, tenant_id: int) -> FieldContext:
        """بناء سياق الحقل للتحليل"""
        field = await self.field_repo.get_field(field_id, tenant_id)
        if not field:
            raise ValueError(f"Field {field_id} not found")

        ndvi_data = await self.ndvi_repo.get_ndvi(field_id, None)

        return FieldContext(
            field_id=field_id,
            tenant_id=tenant_id,
            name=field.name,
            ndvi=NDVIContext(
                mean=ndvi_data.get("mean_ndvi", 0.5) if ndvi_data else 0.5,
                min=ndvi_data.get("min_ndvi", 0.2) if ndvi_data else 0.2,
                max=ndvi_data.get("max_ndvi", 0.8) if ndvi_data else 0.8,
                zones={"low": 0.2, "medium": 0.5, "high": 0.3}
            ),
            weather=WeatherContext(
                tmax=35,
                tmin=22,
                tmean=28,
                rain_mm=0,
                humidity=45,
                wind_speed=12
            ),
            crop=CropContext(
                type=field.crop_type or "unknown",
                growth_stage="vegetative",
                planting_date=None
            )
        )

    async def analyze(self, context: FieldContext) -> List[Recommendation]:
        """تحليل السياق وتوليد التوصيات"""
        recommendations = []

        for rule in self.rules:
            if self._evaluate_conditions(rule["conditions"], context):
                rec = rule["recommendation"]
                recommendations.append(Recommendation(
                    id=str(uuid.uuid4()),
                    rule_name=rule["name"],
                    priority=rule["priority"],
                    title_ar=rec["title_ar"],
                    title_en=rec["title_en"],
                    description_ar=rec["description_ar"],
                    description_en=rec["description_en"],
                    actions=rec["actions"],
                    field_id=context.field_id,
                    timestamp=datetime.utcnow()
                ))

        # ترتيب حسب الأولوية
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 2))

        return recommendations

    def _evaluate_conditions(self, conditions: List[Dict], context: FieldContext) -> bool:
        """تقييم شروط القاعدة"""
        for condition in conditions:
            field_path = condition["field"].split(".")
            value = context

            for path in field_path:
                if hasattr(value, path):
                    value = getattr(value, path)
                elif isinstance(value, dict) and path in value:
                    value = value[path]
                else:
                    return False

            op = condition["operator"]
            target = condition["value"]

            if op == "<" and not (value < target):
                return False
            elif op == ">" and not (value > target):
                return False
            elif op == "==" and not (value == target):
                return False

        return True

    async def get_history(self, field_id: int, tenant_id: int) -> List[Recommendation]:
        """جلب سجل التوصيات"""
        # في التطبيق الحقيقي، يتم جلب من قاعدة البيانات
        return []

    def get_available_rules(self) -> List[str]:
        """جلب قائمة القواعد المتاحة"""
        return [rule["name"] for rule in self.rules]'

# Repository - field
write_file "$PROJECT_NAME/backend/app/repositories/field_repository.py" 'from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.field import Field

class FieldRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_field(self, field_id: int, tenant_id: int) -> Optional[Field]:
        return self.db.query(Field).filter(
            Field.id == field_id,
            Field.tenant_id == tenant_id
        ).first()

    async def get_fields_by_tenant(self, tenant_id: int) -> List[Field]:
        return self.db.query(Field).filter(Field.tenant_id == tenant_id).all()'

# Repository - ndvi
write_file "$PROJECT_NAME/backend/app/repositories/ndvi_repository.py" 'from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import date
from app.models.ndvi import NDVIResult

class NDVIRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_ndvi(self, field_id: int, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        query = self.db.query(NDVIResult).filter(NDVIResult.field_id == field_id)

        if target_date:
            query = query.filter(NDVIResult.date == target_date)
        else:
            query = query.order_by(NDVIResult.date.desc())

        result = query.first()

        if not result:
            return None

        return {
            "field_id": result.field_id,
            "date": str(result.date),
            "mean_ndvi": result.mean_ndvi,
            "min_ndvi": result.min_ndvi,
            "max_ndvi": result.max_ndvi,
            "std_ndvi": result.std_ndvi,
            "pixel_count": result.pixel_count,
            "tile_url": result.tile_url,
            "zones": {
                "low": {"percentage": 30, "area_ha": 15.2},
                "medium": {"percentage": 50, "area_ha": 25.4},
                "high": {"percentage": 20, "area_ha": 10.1}
            }
        }

    async def get_timeline(self, field_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        results = self.db.query(NDVIResult).filter(
            NDVIResult.field_id == field_id,
            NDVIResult.date.between(start_date, end_date)
        ).order_by(NDVIResult.date.asc()).all()

        return [{
            "field_id": r.field_id,
            "date": str(r.date),
            "mean_ndvi": r.mean_ndvi,
            "min_ndvi": r.min_ndvi,
            "max_ndvi": r.max_ndvi,
            "std_ndvi": r.std_ndvi,
            "pixel_count": r.pixel_count,
            "tile_url": r.tile_url,
            "zones": {
                "low": {"percentage": 30, "area_ha": 15.2},
                "medium": {"percentage": 50, "area_ha": 25.4},
                "high": {"percentage": 20, "area_ha": 10.1}
            }
        } for r in results]'

# Models - field
write_file "$PROJECT_NAME/backend/app/models/field.py" 'from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, JSON, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    crop_type = Column(String(100))
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    area_ha = Column(Float)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    metadata = Column(JSON)

    ndvi_results = relationship("NDVIResult", back_populates="field")'

# Models - ndvi
write_file "$PROJECT_NAME/backend/app/models/ndvi.py" 'from sqlalchemy import Column, Integer, ForeignKey, Date, Float, TIMESTAMP, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class NDVIResult(Base):
    __tablename__ = "ndvi_results"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ndvi_value = Column(Float)
    mean_ndvi = Column(Float)
    min_ndvi = Column(Float)
    max_ndvi = Column(Float)
    std_ndvi = Column(Float)
    pixel_count = Column(Integer)
    tile_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default="now()")

    field = relationship("Field", back_populates="ndvi_results")'

# Models - init
write_file "$PROJECT_NAME/backend/app/models/__init__.py" 'from app.models.field import Field
from app.models.ndvi import NDVIResult

__all__ = ["Field", "NDVIResult"]'

# Database
write_file "$PROJECT_NAME/backend/app/core/database.py" 'from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()'

# Dependencies
write_file "$PROJECT_NAME/backend/app/dependencies.py" 'from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.ndvi_service import NDVIService
from app.services.field_service import FieldService
from app.services.advisor_service import AdvisorService
import redis

security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

class MockUser:
    def __init__(self):
        self.id = 1
        self.tenant_id = 1
        self.is_admin = True

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # في الإنتاج: تحقق من JWT الحقيقي
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return MockUser()

def get_redis():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_ndvi_service(db: Session = Depends(get_db)):
    cache = get_redis()
    return NDVIService(db, cache)

def get_field_service(db: Session = Depends(get_db)):
    return FieldService(db)

def get_advisor_service(db: Session = Depends(get_db)):
    cache = get_redis()
    return AdvisorService(db, cache)'

# Main App
write_file "$PROJECT_NAME/backend/app/main.py" 'from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.dependencies import limiter
from app.api.v1 import fields, ndvi, advisor

# إعداد التسجيل
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Field Suite API",
    description="نظام إدارة الحقول الزراعية وتحليل NDVI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(fields.router, prefix="/api/v1", tags=["Fields"])
app.include_router(ndvi.router, prefix="/api/v1", tags=["NDVI"])
app.include_router(advisor.router, prefix="/api/v1", tags=["Advisor"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "مرحباً بك في Field Suite API", "docs": "/docs"}'

# =====================================
# 11️⃣ إنشاء ملفات الواجهة الأمامية
# =====================================
echo -e "${BLUE}⚛️ إنشاء ملفات الواجهة الأمامية...${NC}"

# Package.json
write_file "$PROJECT_NAME/web/package.json" '{
  "name": "field-suite-web",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@tanstack/react-query": "^4.32.0",
    "axios": "^1.4.0",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.2",
    "leaflet": "^1.9.4",
    "@types/leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext ts,tsx"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5",
    "vitest": "^0.33.0"
  }
}'

# Vite Config
write_file "$PROJECT_NAME/web/vite.config.ts" 'import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});'

# TS Config
write_file "$PROJECT_NAME/web/tsconfig.json" '{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}'

# API Client
write_file "$PROJECT_NAME/web/src/api/client.ts" 'import axios, { AxiosInstance } from "axios";

export interface Field {
  id: number;
  tenant_id: number;
  name: string;
  crop_type: string;
  geometry: any;
  area_ha?: number;
  created_at: string;
}

export interface NDVIData {
  field_id: number;
  date: string;
  mean_ndvi: number;
  min_ndvi: number;
  max_ndvi: number;
  std_ndvi: number;
  pixel_count: number;
  zones: {
    low: { percentage: number; area_ha: number };
    medium: { percentage: number; area_ha: number };
    high: { percentage: number; area_ha: number };
  };
  tile_url?: string;
}

export interface Recommendation {
  id: string;
  rule_name: string;
  priority: "critical" | "high" | "medium" | "low";
  title_ar: string;
  title_en: string;
  description_ar: string;
  description_en: string;
  actions: Array<{
    action_ar: string;
    action_en: string;
    urgency: string;
  }>;
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class FieldSuiteAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: { "Content-Type": "application/json" },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  async getFields(): Promise<Field[]> {
    const { data } = await this.client.get("/api/v1/fields");
    return data;
  }

  async getField(fieldId: number): Promise<Field> {
    const { data } = await this.client.get(`/api/v1/fields/${fieldId}`);
    return data;
  }

  async getNDVI(fieldId: number, targetDate?: string): Promise<NDVIData> {
    const params = targetDate ? { target_date: targetDate } : {};
    const { data } = await this.client.get(`/api/v1/ndvi/${fieldId}`, { params });
    return data;
  }

  async analyzeField(fieldId: number): Promise<Recommendation[]> {
    const { data } = await this.client.post("/api/v1/advisor/analyze-field", { field_id: fieldId });
    return data;
  }
}

export const api = new FieldSuiteAPI();'

# App Component
write_file "$PROJECT_NAME/web/src/App.tsx" 'import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import FieldDetails from "./pages/FieldDetails";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-100" dir="rtl">
          <nav className="bg-green-600 text-white p-4">
            <h1 className="text-2xl font-bold">🌾 Field Suite</h1>
          </nav>
          <main className="container mx-auto p-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/fields/:id" element={<FieldDetails />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;'

# Main entry
write_file "$PROJECT_NAME/web/src/main.tsx" 'import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'

# CSS
write_file "$PROJECT_NAME/web/src/index.css" '@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: "Cairo", sans-serif;
  direction: rtl;
}'

# HTML
write_file "$PROJECT_NAME/web/index.html" '<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <title>Field Suite - نظام إدارة الحقول</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'

# Dashboard Page
write_file "$PROJECT_NAME/web/src/pages/Dashboard.tsx" 'import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";

const Dashboard: React.FC = () => {
  const { data: fields, isLoading, error } = useQuery({
    queryKey: ["fields"],
    queryFn: () => api.getFields(),
  });

  if (isLoading) {
    return <div className="text-center p-8">جاري التحميل...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-8">حدث خطأ في تحميل البيانات</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">الحقول</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {fields?.map((field) => (
          <Link
            key={field.id}
            to={`/fields/${field.id}`}
            className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition"
          >
            <h3 className="text-lg font-semibold">{field.name}</h3>
            <p className="text-gray-600">المحصول: {field.crop_type}</p>
            {field.area_ha && (
              <p className="text-gray-500">المساحة: {field.area_ha.toFixed(2)} هكتار</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;'

# Field Details Page
write_file "$PROJECT_NAME/web/src/pages/FieldDetails.tsx" 'import React from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import AdvisorPanel from "../components/advisor/AdvisorPanel";

const FieldDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const fieldId = parseInt(id || "0");

  const { data: field, isLoading } = useQuery({
    queryKey: ["field", fieldId],
    queryFn: () => api.getField(fieldId),
    enabled: !!fieldId,
  });

  const { data: ndvi } = useQuery({
    queryKey: ["ndvi", fieldId],
    queryFn: () => api.getNDVI(fieldId),
    enabled: !!fieldId,
  });

  if (isLoading) {
    return <div className="text-center p-8">جاري التحميل...</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">{field?.name}</h2>
          <p className="text-gray-600">المحصول: {field?.crop_type}</p>
          {field?.area_ha && (
            <p className="text-gray-500">المساحة: {field.area_ha.toFixed(2)} هكتار</p>
          )}
        </div>

        {ndvi && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">بيانات NDVI</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">
                  {ndvi.mean_ndvi.toFixed(3)}
                </div>
                <div className="text-sm text-gray-600">المتوسط</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {ndvi.max_ndvi.toFixed(3)}
                </div>
                <div className="text-sm text-gray-600">الأعلى</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <AdvisorPanel fieldId={fieldId} />
      </div>
    </div>
  );
};

export default FieldDetails;'

# Advisor Panel Component
write_file "$PROJECT_NAME/web/src/components/advisor/AdvisorPanel.tsx" 'import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

interface AdvisorPanelProps {
  fieldId: number;
}

const AdvisorPanel: React.FC<AdvisorPanelProps> = ({ fieldId }) => {
  const { data: recommendations, isLoading, refetch } = useQuery({
    queryKey: ["advisor", fieldId],
    queryFn: () => api.analyzeField(fieldId),
    enabled: !!fieldId,
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical": return "border-red-500 bg-red-50";
      case "high": return "border-orange-500 bg-orange-50";
      case "medium": return "border-yellow-500 bg-yellow-50";
      default: return "border-green-500 bg-green-50";
    }
  };

  if (isLoading) {
    return <div className="text-center p-4">جاري تحليل الحقل...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">التوصيات</h3>
        <button
          onClick={() => refetch()}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          تحديث
        </button>
      </div>

      {!recommendations?.length ? (
        <p className="text-gray-500">لا توجد توصيات حالياً</p>
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className={`p-4 rounded-lg border-r-4 ${getPriorityColor(rec.priority)}`}
            >
              <h4 className="font-semibold">{rec.title_ar}</h4>
              <p className="text-sm text-gray-600 mt-1">{rec.description_ar}</p>
              {rec.actions.length > 0 && (
                <ul className="mt-2 text-sm">
                  {rec.actions.map((action, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <span className="text-green-600">•</span>
                      {action.action_ar}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdvisorPanel;'

# =====================================
# 12️⃣ إنشاء Docker files
# =====================================
echo -e "${BLUE}🐳 إنشاء ملفات Docker...${NC}"

# Backend Dockerfile
write_file "$PROJECT_NAME/backend/Dockerfile" 'FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'

# Requirements
write_file "$PROJECT_NAME/backend/requirements.txt" 'fastapi==0.100.0
uvicorn[standard]==0.22.0
sqlalchemy==2.0.18
alembic==1.11.1
geoalchemy2==0.14.1
psycopg2-binary==2.9.6
redis==4.6.0
celery==5.3.1
pydantic==1.10.11
python-jose[cryptography]==3.3.0
slowapi==0.1.8
python-multipart==0.0.6
httpx==0.24.1
numpy==1.25.1
rasterio==1.3.8'

# Web Dockerfile
write_file "$PROJECT_NAME/web/Dockerfile" 'FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'

# Nginx config
write_file "$PROJECT_NAME/web/nginx.conf" 'server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}'

# Docker Compose
write_file "$PROJECT_NAME/docker-compose.yml" 'version: "3.8"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/field_suite_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build: ./web
    ports:
      - "3000:80"
    depends_on:
      - api

  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: field_suite_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:'

# .env.example
write_file "$PROJECT_NAME/.env.example" '# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=field_suite_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# APIs
OPENWEATHER_API_KEY=
SENTINEL_CLIENT_ID=
SENTINEL_CLIENT_SECRET=

# Environment
ENV=development
DEBUG=true'

# =====================================
# 13️⃣ إنشاء سكريبتات المساعدة
# =====================================
echo -e "${BLUE}📜 إنشاء سكريبتات المساعدة...${NC}"

write_file "$PROJECT_NAME/scripts/start.sh" '#!/bin/bash
echo "🚀 تشغيل Field Suite..."
cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️ تم إنشاء ملف .env - يرجى تعديله"
fi

docker-compose up -d --build

echo "⏳ انتظار بدء الخدمات..."
sleep 15

echo "✅ Field Suite يعمل على:"
echo "   🌐 Frontend: http://localhost:3000"
echo "   🔌 API: http://localhost:8000/docs"'

write_file "$PROJECT_NAME/scripts/stop.sh" '#!/bin/bash
echo "🛑 إيقاف Field Suite..."
cd "$(dirname "$0")/.."
docker-compose down
echo "✅ تم الإيقاف"'

write_file "$PROJECT_NAME/scripts/health-check.sh" '#!/bin/bash
echo "🔍 فحص صحة الخدمات..."

services=("api" "web" "db" "redis")
for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service: يعمل"
    else
        echo "❌ $service: متوقف"
    fi
done'

# =====================================
# 14️⃣ إعطاء صلاحيات التنفيذ
# =====================================
chmod +x "$PROJECT_NAME/scripts/"*.sh

# =====================================
# 15️⃣ إنشاء README
# =====================================
write_file "$PROJECT_NAME/README.md" '# 🌾 Field Suite

نظام متكامل لإدارة الحقول الزراعية وتحليل صحة المحاصيل

## المميزات

- ✅ إدارة الحقول الزراعية
- ✅ تحليل NDVI للصور الفضائية
- ✅ نظام توصيات ذكي (Advisor)
- ✅ واجهة مستخدم عربية
- ✅ API موثق بالكامل

## التشغيل السريع

```bash
./scripts/start.sh
```

## الروابط

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc

## البنية

```
field_suite_complete/
├── backend/          # FastAPI Backend
├── web/              # React Frontend
├── scripts/          # Helper Scripts
└── docker-compose.yml
```

## التقنيات

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: React, TypeScript, TanStack Query
- **Infrastructure**: Docker, Nginx
'

# =====================================
# النهاية
# =====================================
echo -e "${GREEN}✅ تم إنشاء مشروع Field Suite بنجاح!${NC}"
echo ""
echo -e "📁 المسار: ${BLUE}$PROJECT_NAME${NC}"
echo ""
echo -e "للتشغيل:"
echo -e "  ${BLUE}cd $PROJECT_NAME${NC}"
echo -e "  ${BLUE}./scripts/start.sh${NC}"
echo ""
echo -e "الروابط:"
echo -e "  🌐 Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "  🔌 API Docs: ${BLUE}http://localhost:8000/docs${NC}"

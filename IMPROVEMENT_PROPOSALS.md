# 🚀 مقترحات التحسين والتطوير الشاملة

## Sahool Field Suite Platform - Improvement Roadmap

---

## 📊 ملخص تنفيذي

بناءً على التحليل التقني الشامل للمشروع، تم تحديد **47 فرصة تحسين** موزعة على:

| الفئة | عدد المقترحات | الأولوية |
|-------|---------------|----------|
| 🔴 الأمان | 13 | حرجة |
| 🟠 الأداء | 12 | عالية |
| 🟡 الاختبارات | 6 | عالية |
| 🔵 الميزات | 10 | متوسطة |
| 🟢 البنية التحتية | 6 | متوسطة |

---

## 🔴 مقترحات الأمان (الأولوية القصوى)

### 1. تنفيذ نظام المصادقة JWT

```python
# الوضع الحالي: لا يوجد مصادقة
# المقترح: JWT + OAuth2

from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

# إعدادات الأمان
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id
```

**التأثير المتوقع:**
- ✅ حماية جميع نقاط النهاية
- ✅ تتبع المستخدمين والجلسات
- ✅ فصل صلاحيات الوصول

---

### 2. التحقق من صحة الملفات المرفوعة

```python
# الوضع الحالي: لا يوجد تحقق
# المقترح:

from fastapi import UploadFile, HTTPException
import magic  # python-magic للتحقق من نوع الملف

class FileValidator:
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {".tif", ".tiff", ".jp2"}
    ALLOWED_MIMES = {"image/tiff", "image/jp2"}

    @classmethod
    async def validate(cls, file: UploadFile) -> bool:
        # التحقق من الحجم
        content = await file.read()
        if len(content) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"حجم الملف أكبر من {cls.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # التحقق من النوع
        mime_type = magic.from_buffer(content[:2048], mime=True)
        if mime_type not in cls.ALLOWED_MIMES:
            raise HTTPException(
                status_code=415,
                detail=f"نوع الملف غير مدعوم: {mime_type}"
            )

        # إعادة المؤشر للبداية
        await file.seek(0)
        return True

# الاستخدام:
@router.post("/upload-bands")
async def upload_bands(
    red_band: UploadFile,
    nir_band: UploadFile
):
    await FileValidator.validate(red_band)
    await FileValidator.validate(nir_band)
    # ... معالجة الملفات
```

**التأثير المتوقع:**
- ✅ منع رفع ملفات ضارة
- ✅ حماية من استنزاف القرص
- ✅ ضمان سلامة البيانات

---

### 3. تقييد CORS

```python
# الوضع الحالي:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ خطير!
)

# المقترح:
ALLOWED_ORIGINS = [
    "https://sahool.app",
    "https://admin.sahool.app",
    "http://localhost:5173",  # للتطوير فقط
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 4. تحديد معدل الطلبات (Rate Limiting)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/analyze-field")
@limiter.limit("10/minute")  # 10 طلبات/دقيقة
async def analyze_field(request: Request, ...):
    ...

@router.post("/ndvi-detect")
@limiter.limit("5/minute")  # العمليات الثقيلة
async def ndvi_detect(request: Request, ...):
    ...
```

---

### 5. معالجة الاستثناءات المحددة

```python
# الوضع الحالي:
try:
    # كود
except:  # ⚠️ يلتقط كل شيء!
    continue

# المقترح:
from shapely.errors import GEOSException
from rasterio.errors import RasterioIOError

try:
    geom = wkt.loads(field.geom_wkt)
    ndvi_data = rasterio.open(raster_path)
except GEOSException as e:
    logger.error(f"خطأ في الهندسة: {e}")
    raise HTTPException(400, f"هندسة غير صالحة: {str(e)}")
except RasterioIOError as e:
    logger.error(f"خطأ في قراءة الصورة: {e}")
    raise HTTPException(400, f"فشل قراءة الملف: {str(e)}")
except Exception as e:
    logger.exception("خطأ غير متوقع")
    raise HTTPException(500, "حدث خطأ داخلي")
```

---

## 🟠 مقترحات تحسين الأداء

### 6. تنفيذ التخزين المؤقت Redis

```python
# إعداد Redis
import aioredis
from functools import wraps

redis = aioredis.from_url("redis://localhost:6379")

def cache(ttl: int = 300):
    """مُزخرف للتخزين المؤقت"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # إنشاء مفتاح فريد
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # محاولة جلب من الكاش
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # تنفيذ الدالة
            result = await func(*args, **kwargs)

            # تخزين في الكاش
            await redis.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# الاستخدام:
@cache(ttl=600)  # 10 دقائق
async def get_field_data(field_id: str):
    return await db.query(Field).filter(Field.id == field_id).first()

@cache(ttl=3600)  # ساعة
async def get_weather_data(lat: float, lon: float):
    return await weather_api.fetch(lat, lon)
```

**التأثير المتوقع:**
```
قبل: 200ms (database query)
بعد: 5ms (cache hit)
تحسين: 40x أسرع
نسبة Cache Hit المتوقعة: 80%+
```

---

### 7. SQLAlchemy غير متزامن

```python
# الوضع الحالي: متزامن
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)

# المقترح: غير متزامن
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# تغيير URL للـ async
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# الاستخدام:
@router.get("/fields")
async def get_fields(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Field))
    return result.scalars().all()
```

**التأثير المتوقع:**
```
قبل: طلب واحد يحجز thread
بعد: آلاف الطلبات المتزامنة
تحسين Throughput: 5-10x
```

---

### 8. معالجة الصور بالقطع (Chunked Processing)

```python
import numpy as np
from rasterio.windows import Window
from concurrent.futures import ThreadPoolExecutor

class OptimizedNDVIProcessor:
    CHUNK_SIZE = 1024  # بكسل
    MAX_WORKERS = 4

    @classmethod
    async def compute_ndvi_chunked(cls, red_path: str, nir_path: str):
        """معالجة NDVI بالقطع للصور الكبيرة"""

        with rasterio.open(red_path) as red_src, \
             rasterio.open(nir_path) as nir_src:

            height, width = red_src.height, red_src.width
            ndvi_result = np.zeros((height, width), dtype=np.float32)

            # تقسيم الصورة لقطع
            windows = []
            for i in range(0, height, cls.CHUNK_SIZE):
                for j in range(0, width, cls.CHUNK_SIZE):
                    w = Window(
                        j, i,
                        min(cls.CHUNK_SIZE, width - j),
                        min(cls.CHUNK_SIZE, height - i)
                    )
                    windows.append(w)

            # معالجة متوازية
            with ThreadPoolExecutor(max_workers=cls.MAX_WORKERS) as executor:
                futures = []
                for window in windows:
                    future = executor.submit(
                        cls._process_chunk,
                        red_src, nir_src, window
                    )
                    futures.append((window, future))

                for window, future in futures:
                    chunk_ndvi = future.result()
                    ndvi_result[
                        window.row_off:window.row_off + window.height,
                        window.col_off:window.col_off + window.width
                    ] = chunk_ndvi

            return ndvi_result

    @staticmethod
    def _process_chunk(red_src, nir_src, window):
        """معالجة قطعة واحدة"""
        red = red_src.read(1, window=window).astype(np.float32)
        nir = nir_src.read(1, window=window).astype(np.float32)

        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = (nir - red) / (nir + red)
            ndvi = np.nan_to_num(ndvi, nan=0, posinf=1, neginf=-1)

        return ndvi
```

**التأثير المتوقع:**
```
صورة 10000x10000 بكسل:
قبل: 45 ثانية (ذاكرة: 2GB)
بعد: 12 ثانية (ذاكرة: 256MB)
تحسين: 4x أسرع، 8x أقل ذاكرة
```

---

### 9. فهارس قاعدة البيانات

```python
# إضافة فهارس للاستعلامات الشائعة

from sqlalchemy import Index

class Field(Base):
    __tablename__ = "fields"

    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime)

    # فهارس مركبة
    __table_args__ = (
        Index('idx_field_tenant', 'tenant_id'),
        Index('idx_field_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_field_name_search', 'name', postgresql_using='gin',
              postgresql_ops={'name': 'gin_trgm_ops'}),  # للبحث النصي
    )

class Recommendation(Base):
    __tablename__ = "recommendations"

    __table_args__ = (
        Index('idx_rec_session', 'session_id'),
        Index('idx_rec_field_status', 'field_id', 'status'),
        Index('idx_rec_priority_created', 'priority', 'created_at'),
    )
```

**التأثير المتوقع:**
```
استعلام بدون فهرس: 500ms (full scan)
استعلام مع فهرس: 5ms (index seek)
تحسين: 100x
```

---

### 10. ضغط استجابات API

```python
from fastapi.middleware.gzip import GZIPMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# ضغط GZIP للاستجابات الكبيرة
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# تبسيط GeoJSON للاستجابات
class GeoJSONSimplifier:
    @staticmethod
    def simplify_geometry(geojson: dict, tolerance: float = 0.0001):
        """تبسيط الهندسة لتقليل الحجم"""
        from shapely.geometry import shape
        from shapely.ops import transform

        geom = shape(geojson)
        simplified = geom.simplify(tolerance, preserve_topology=True)
        return simplified.__geo_interface__

# الاستخدام:
@router.get("/zones/{field_id}")
async def get_zones(field_id: str, simplify: bool = True):
    zones = await get_field_zones(field_id)

    if simplify:
        for zone in zones:
            zone["geometry"] = GeoJSONSimplifier.simplify_geometry(
                zone["geometry"]
            )

    return zones
```

**التأثير المتوقع:**
```
حجم الاستجابة:
قبل: 500KB (GeoJSON كامل)
بعد: 50KB (مبسط + مضغوط)
تحسين: 90% توفير في النطاق الترددي
```

---

## 🟡 مقترحات الاختبارات

### 11. زيادة تغطية الاختبارات

```python
# tests/test_ndvi_service.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

class TestNDVIService:
    """اختبارات خدمة NDVI"""

    @pytest.fixture
    def mock_raster_data(self):
        """بيانات اختبار"""
        return {
            "red": np.array([[100, 150], [200, 250]], dtype=np.float32),
            "nir": np.array([[200, 300], [400, 500]], dtype=np.float32),
            "expected_ndvi": np.array([[0.333, 0.333], [0.333, 0.333]], dtype=np.float32)
        }

    def test_ndvi_calculation_normal(self, mock_raster_data):
        """اختبار حساب NDVI العادي"""
        red = mock_raster_data["red"]
        nir = mock_raster_data["nir"]

        ndvi = (nir - red) / (nir + red)

        assert ndvi.shape == (2, 2)
        assert -1 <= ndvi.min() <= 1
        assert -1 <= ndvi.max() <= 1

    def test_ndvi_division_by_zero(self):
        """اختبار القسمة على صفر"""
        red = np.array([[0, 100]], dtype=np.float32)
        nir = np.array([[0, 200]], dtype=np.float32)

        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = (nir - red) / (nir + red)
            ndvi = np.nan_to_num(ndvi, nan=0)

        assert ndvi[0, 0] == 0  # 0/0 = nan -> 0

    def test_ndvi_negative_values(self):
        """اختبار القيم السالبة (ماء)"""
        red = np.array([[200]], dtype=np.float32)
        nir = np.array([[100]], dtype=np.float32)

        ndvi = (nir - red) / (nir + red)

        assert ndvi[0, 0] < 0  # الماء له NDVI سالب

    @pytest.mark.parametrize("threshold,expected_zones", [
        (0.3, 3),  # عتبة منخفضة = مناطق أكثر
        (0.5, 2),  # عتبة متوسطة
        (0.7, 1),  # عتبة عالية = مناطق أقل
    ])
    def test_zone_detection_thresholds(self, threshold, expected_zones):
        """اختبار كشف المناطق بعتبات مختلفة"""
        # ... تنفيذ الاختبار


class TestAdvisorRulesEngine:
    """اختبارات محرك القواعد"""

    @pytest.fixture
    def rules_engine(self):
        return RulesEngine()

    def test_low_ndvi_triggers_irrigation(self, rules_engine):
        """NDVI منخفض يُطلق توصية ري"""
        context = {
            "ndvi": {"mean": 0.25, "std": 0.1},
            "weather": {"temperature": 30}
        }

        recommendations = rules_engine.evaluate(context)

        irrigation_recs = [r for r in recommendations if r["category"] == "irrigation"]
        assert len(irrigation_recs) > 0
        assert irrigation_recs[0]["priority"] in ["high", "critical"]

    def test_high_temp_triggers_alert(self, rules_engine):
        """حرارة عالية تُطلق تنبيه"""
        context = {
            "ndvi": {"mean": 0.6},
            "weather": {"temperature": 42}
        }

        recommendations = rules_engine.evaluate(context)

        assert any(r["priority"] == "high" for r in recommendations)


class TestAPIEndpoints:
    """اختبارات نقاط النهاية"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_analyze_field_success(self, client):
        """اختبار تحليل حقل بنجاح"""
        response = client.post("/api/advisor/analyze-field", json={
            "field_id": "test-field-001",
            "ndvi_data": {"mean": 0.6, "std": 0.1}
        })

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "alerts" in data
        assert "overall_health_score" in data

    def test_analyze_field_invalid_input(self, client):
        """اختبار إدخال غير صالح"""
        response = client.post("/api/advisor/analyze-field", json={
            "field_id": ""  # فارغ
        })

        assert response.status_code == 422  # Validation Error

    def test_health_check(self, client):
        """اختبار نقطة الصحة"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

---

### 12. اختبارات التحميل (Load Testing)

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between

class FieldAnalysisUser(HttpUser):
    """مستخدم اختبار التحميل"""
    wait_time = between(1, 3)

    @task(3)
    def analyze_field(self):
        """تحليل حقل - الأكثر استخداماً"""
        self.client.post("/api/advisor/analyze-field", json={
            "field_id": f"field-{self.user_id}",
            "ndvi_data": {"mean": 0.55, "std": 0.12}
        })

    @task(2)
    def get_recommendations(self):
        """جلب التوصيات"""
        self.client.get("/api/advisor/recommendations?field_id=field-001")

    @task(1)
    def health_check(self):
        """فحص الصحة"""
        self.client.get("/health")

# التشغيل:
# locust -f tests/load/locustfile.py --host=http://localhost:8000
```

**الأهداف:**
```
المستخدمون المتزامنون: 100
معدل الطلبات: 500/ثانية
زمن الاستجابة p95: <200ms
معدل الخطأ: <0.1%
```

---

## 🔵 مقترحات الميزات الجديدة

### 13. WebSocket للتحديثات الفورية

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    """إدارة اتصالات WebSocket"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, field_id: str):
        await websocket.accept()
        if field_id not in self.active_connections:
            self.active_connections[field_id] = set()
        self.active_connections[field_id].add(websocket)

    def disconnect(self, websocket: WebSocket, field_id: str):
        self.active_connections[field_id].discard(websocket)

    async def broadcast_to_field(self, field_id: str, message: dict):
        """بث رسالة لجميع المتصلين بحقل معين"""
        if field_id in self.active_connections:
            for connection in self.active_connections[field_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/field/{field_id}")
async def websocket_endpoint(websocket: WebSocket, field_id: str):
    await manager.connect(websocket, field_id)
    try:
        while True:
            data = await websocket.receive_json()

            # معالجة الرسائل الواردة
            if data.get("type") == "request_analysis":
                # بدء التحليل وإرسال التحديثات
                await manager.broadcast_to_field(field_id, {
                    "type": "analysis_started",
                    "progress": 0
                })

                # ... تنفيذ التحليل مع تحديثات دورية

                await manager.broadcast_to_field(field_id, {
                    "type": "analysis_complete",
                    "progress": 100,
                    "results": {...}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, field_id)
```

**الفوائد:**
- ✅ تحديثات فورية للتحليل
- ✅ تقليل polling
- ✅ تجربة مستخدم أفضل

---

### 14. نظام الإشعارات

```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional
import aiosmtplib
from twilio.rest import Client

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationService:
    """خدمة الإشعارات الموحدة"""

    def __init__(self):
        self.email_client = aiosmtplib.SMTP(...)
        self.sms_client = Client(TWILIO_SID, TWILIO_TOKEN)
        self.push_client = firebase_admin.messaging

    async def send(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: str = "normal",
        data: Optional[dict] = None
    ):
        """إرسال إشعار"""

        # تسجيل الإشعار
        notification = await self._log_notification(
            user_id, title, message, notification_type
        )

        if notification_type == NotificationType.EMAIL:
            await self._send_email(user_id, title, message)
        elif notification_type == NotificationType.SMS:
            await self._send_sms(user_id, message)
        elif notification_type == NotificationType.PUSH:
            await self._send_push(user_id, title, message, data)
        elif notification_type == NotificationType.IN_APP:
            await self._send_in_app(user_id, title, message)

        return notification

    async def send_alert(self, alert: Alert):
        """إرسال تنبيه زراعي"""
        user_prefs = await self._get_user_preferences(alert.user_id)

        # تحديد قنوات الإرسال حسب الأولوية
        channels = []
        if alert.type == "critical":
            channels = [NotificationType.SMS, NotificationType.PUSH, NotificationType.EMAIL]
        elif alert.type == "warning":
            channels = [NotificationType.PUSH, NotificationType.EMAIL]
        else:
            channels = [NotificationType.IN_APP]

        for channel in channels:
            if user_prefs.get(channel.value, True):
                await self.send(
                    user_id=alert.user_id,
                    title=alert.title,
                    message=alert.message,
                    notification_type=channel,
                    priority=alert.type
                )
```

---

### 15. تصدير البيانات

```python
import csv
import io
from openpyxl import Workbook
from fastapi.responses import StreamingResponse

class ExportService:
    """خدمة تصدير البيانات"""

    @staticmethod
    async def export_recommendations_csv(
        field_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> StreamingResponse:
        """تصدير التوصيات كـ CSV"""

        recommendations = await get_recommendations(field_id, start_date, end_date)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "التاريخ", "الفئة", "الأولوية", "العنوان", "الوصف", "الحالة"
        ])
        writer.writeheader()

        for rec in recommendations:
            writer.writerow({
                "التاريخ": rec.created_at.strftime("%Y-%m-%d"),
                "الفئة": rec.category,
                "الأولوية": rec.priority,
                "العنوان": rec.title,
                "الوصف": rec.description,
                "الحالة": rec.status
            })

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=recommendations_{field_id}.csv"
            }
        )

    @staticmethod
    async def export_field_report_pdf(field_id: str) -> bytes:
        """تصدير تقرير الحقل كـ PDF"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, Paragraph

        # ... إنشاء PDF

    @staticmethod
    async def export_zones_geojson(field_id: str) -> dict:
        """تصدير المناطق كـ GeoJSON"""
        zones = await get_field_zones(field_id)

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": zone.geometry,
                    "properties": {
                        "zone_id": zone.id,
                        "ndvi_mean": zone.ndvi_mean,
                        "health_status": zone.health_status
                    }
                }
                for zone in zones
            ]
        }
```

---

### 16. لوحة تحكم المدير

```typescript
// web/src/pages/AdminDashboard.tsx

import React, { useState, useEffect } from 'react';
import { LineChart, BarChart, PieChart } from 'recharts';

interface SystemMetrics {
  activeUsers: number;
  totalFields: number;
  analysisToday: number;
  avgResponseTime: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
}

const AdminDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // كل 30 ثانية
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="admin-dashboard p-6">
      <h1 className="text-2xl font-bold mb-6">لوحة تحكم النظام</h1>

      {/* مؤشرات الأداء الرئيسية */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="المستخدمون النشطون"
          value={metrics?.activeUsers}
          icon="👥"
        />
        <MetricCard
          title="التحليلات اليوم"
          value={metrics?.analysisToday}
          icon="📊"
        />
        <MetricCard
          title="متوسط الاستجابة"
          value={`${metrics?.avgResponseTime}ms`}
          icon="⚡"
        />
        <MetricCard
          title="معدل الأخطاء"
          value={`${metrics?.errorRate}%`}
          icon="⚠️"
          alert={metrics?.errorRate > 1}
        />
      </div>

      {/* رسوم بيانية */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">طلبات API (آخر 24 ساعة)</h3>
          <LineChart data={apiRequestsData} />
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">توزيع التوصيات</h3>
          <PieChart data={recommendationsData} />
        </div>
      </div>

      {/* التنبيهات */}
      <div className="mt-6 bg-white rounded-lg shadow p-4">
        <h3 className="font-semibold mb-4">تنبيهات النظام</h3>
        <AlertsList alerts={alerts} />
      </div>
    </div>
  );
};
```

---

## 🟢 مقترحات البنية التحتية

### 17. CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.3
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linters
        run: |
          pip install ruff black mypy
          ruff check .
          black --check .
          mypy app/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security scan
        run: |
          pip install bandit safety
          bandit -r app/
          safety check

  build:
    needs: [test, lint, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t sahool/field-advisor:${{ github.sha }} .

      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          docker push sahool/field-advisor:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Kubernetes deployment
          kubectl set image deployment/field-advisor \
            field-advisor=sahool/field-advisor:${{ github.sha }}
```

---

### 18. Kubernetes Deployment

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: field-advisor
  labels:
    app: field-advisor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: field-advisor
  template:
    metadata:
      labels:
        app: field-advisor
    spec:
      containers:
        - name: field-advisor
          image: sahool/field-advisor:latest
          ports:
            - containerPort: 8001
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: field-advisor-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: field-advisor-secrets
                  key: redis-url

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: field-advisor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: field-advisor
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

### 19. المراقبة والتنبيهات

```yaml
# prometheus/alerts.yml

groups:
  - name: field-advisor-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "معدل أخطاء عالي في Field Advisor"
          description: "معدل الأخطاء {{ $value | humanizePercentage }} خلال آخر 5 دقائق"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "زمن استجابة عالي"
          description: "p95 زمن الاستجابة {{ $value | humanizeDuration }}"

      - alert: LowNDVIDetected
        expr: avg(field_ndvi_mean) < 0.3
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "NDVI منخفض مكتشف"
          description: "متوسط NDVI للحقول {{ $value }}"

      - alert: DatabaseConnectionFailure
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "فشل الاتصال بقاعدة البيانات"
```

---

## 📅 خارطة طريق التنفيذ

### المرحلة 1: الأمان (أسبوع 1-2)
```
□ تنفيذ JWT Authentication
□ إضافة التحقق من الملفات
□ تقييد CORS
□ إضافة Rate Limiting
□ إصلاح معالجة الاستثناءات
```

### المرحلة 2: الأداء (أسبوع 3-4)
```
□ تنفيذ Redis Caching
□ تحويل إلى Async SQLAlchemy
□ إضافة فهارس قاعدة البيانات
□ تحسين معالجة الصور
□ إضافة ضغط الاستجابات
```

### المرحلة 3: الاختبارات (أسبوع 5-6)
```
□ زيادة Unit Tests إلى 80%+
□ إضافة Integration Tests
□ إعداد Load Testing
□ إضافة Security Tests
```

### المرحلة 4: الميزات (أسبوع 7-10)
```
□ إضافة WebSocket
□ تنفيذ نظام الإشعارات
□ إضافة Export Service
□ إنشاء Admin Dashboard
□ إضافة API Versioning
```

### المرحلة 5: البنية التحتية (أسبوع 11-12)
```
□ إعداد CI/CD
□ إنشاء Kubernetes manifests
□ تكوين Monitoring
□ إعداد Logging المركزي
```

---

## 📊 مؤشرات النجاح

| المؤشر | الحالي | الهدف |
|--------|--------|-------|
| تغطية الاختبارات | ~30% | 80%+ |
| زمن الاستجابة p95 | 500ms | <200ms |
| معدل الأخطاء | ~2% | <0.1% |
| Uptime | 95% | 99.9% |
| Cache Hit Rate | 0% | 80%+ |
| Security Score | 40/100 | 90/100 |

---

*تم إنشاء هذه الوثيقة: 2025-12-02*
*المشروع: Sahool Field Suite Platform*
*الإصدار: 1.0*

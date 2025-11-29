# Sahool Platform – Enterprise Architecture (v15)

## 1. Overview

منصة **سهول** هي منصة زراعية ذكية مبنية على معمارية **Microservices + API Gateway + Frontend (Next.js)**
ومجهزة للعمل في بيئات Kubernetes/Containers مع قابلية للتوسع والدمج مع مصادر بيانات خارجية
(الأقمار الصناعية، الطقس، التربة، وتحليلات الذكاء الاصطناعي).

المكونات الرئيسية:

- Core Services: geo, imagery, weather, soil, analytics, alerts, timeline
- Ingestors: satellite-ingestor, weather-ingestor, ndvi-processor
- AI: agent-ai (Field Assistant)
- Edge: gateway-edge (API gateway & routing)
- Frontend: web (Next.js Farmer Dashboard)
- Infra: Docker Compose + Helm charts

## 2. Core Services

### 2.1 geo-core

مسؤول عن:
- إدارة الحقول (Fields) متعددة المستأجرين (multi-tenant)
- حفظ الـ geometry في PostGIS (MULTIPOLYGON, EPSG:4326)
- حساب:
  - المساحة (area_ha)
  - الإحداثيات المركزية (centroid_lat, centroid_lon)
  - المشتقات الإضافية:
    - bbox (Bounding Box)
    - centroid_geojson (Point GeoJSON)

Endpoints مهمة:
- `GET /api/v1/fields?tenant_id=...`
- `GET /api/v1/fields/{field_id}?tenant_id=...`
- `POST /api/v1/fields`
- `PUT /api/v1/fields/{field_id}`
- `GET /health`, `GET /info`

### 2.2 imagery-core

مسؤول عن:
- تخزين metadata لصور الأقمار الصناعية (SatelliteImage)
- ربط كل صورة:
  - tenant_id
  - field_id
  - scene_id (من CDSE أو مصدر آخر)
  - product_name
  - timestamp
  - cloudcover
  - ndvi_path / raw_zip (مسارات المعالجة)

Endpoints:
- `GET /api/v1/images?tenant_id=...&field_id=...`
- `POST /api/v1/imagery/ingest`
- `GET /health`, `GET /info`

يتكامل مع:
- `satellite-ingestor` (عن طريق gateway-edge)
- `ndvi-processor` مستقبلاً لمعالجة الصور وحساب NDVI.

### 2.3 weather-core

مسؤول عن:
- حفظ بيانات الطقس المتوقعة/المقاسة لكل حقل:
  - timestamp
  - temp_c
  - eto_mm
  - rain_mm
  - wind_speed_ms
  - rel_humidity_pct

Endpoints:
- `GET /api/v1/weather/forecast?tenant_id=...&field_id=...`
- `POST /api/v1/weather/ingest`
- `GET /health`, `GET /info`

يتم تغذيته بواسطة:
- `weather-ingestor` (Open-Meteo أو مزود آخر).

### 2.4 soil-core

مسؤول عن:
- خصائص التربة لكل حقل / نقطة:
  - EC, pH, Texture, etc.

يستخدمها analytics-core لحساب مؤشرات الصحة والضغط.

### 2.5 analytics-core

مسؤول عن:
- حساب Health & Stress Indicators بناءً على:
  - NDVI
  - Soil (pH, EC)
  - Weather (ETo, Temp, Rain)
- توليد توصيات (Insights) للمزارع/المنصة.

الخدمة تستخدم دوال مثل:
- `compute_health(ndvi, ph, ec, eto)`
  - تحسب ndvi_score, soil_score, weather_score, total_health
  - المعاملات قابلة للضبط عبر الإعدادات (config).

- `compute_stress(ec, eto, temp)`
- `generate_insights(health, stress)`

### 2.6 alerts-core

مسؤول عن:
- تخزين وتنظيم التنبيهات لكل حقل:
  - نوع التنبيه (ملوحة، جفاف، حرارة، NDVI drop)
  - مستوى الخطورة
  - timestamp
- يتم استعراضها في الواجهة (Alerts tab).

### 2.7 timeline-core

مسؤول عن:
- تجميع خط زمني موحد لكل حقل من مصادر متعددة:
  - weather-core (ETo, rain, temp)
  - imagery-core (NDVI)
  - soil-core (مؤشرات تربة لاحقاً)

Endpoint:
- `GET /api/v1/timeline/field/{field_id}?tenant_id=...`

يستدعي:
- `gateway-edge -> weather-core` للحصول على forecast/series.
- مستقبلاً: `imagery-core` و `soil-core` لتغذية NDVI وبيانات التربة.

## 3. Ingestors

### 3.1 satellite-ingestor

دوره:
- الاتصال بـ Copernicus Data Space Ecosystem (CDSE) باستخدام OData.
- البحث عن مشاهد Sentinel-2 بناءً على:
  - AOI (من geo-core)
  - فترة زمنية
- إرسال metadata إلى imagery-core عبر gateway-edge.

خط الأنابيب:
1) `GET geo-core /fields/{field_id}` (للحصول على centroid/geometry)
2) `CDSEClient.search_sentinel2(...)`
3) `POST gateway-edge /api/imagery/api/v1/imagery/ingest`

### 3.2 ndvi-processor

دوره:
- حساب NDVI من ملفات GeoTIFF:
  - `compute_ndvi_from_tif(path, red_band=3, nir_band=4)`
- يعيد إحصاءات (NDVIStats):
  - mean / min / max

يمكن استخدامه في مهام:
- Batch processing لكل مشهد بعد تنزيله من CDSE.
- تحديث imagery-core/timeline-core بقيم NDVI.

### 3.3 weather-ingestor

دوره:
- جلب بيانات طقس لكل حقل من مزود مثل Open-Meteo:
  - temperature_2m, precipitation ...
- تحويلها إلى قائمة WeatherPoint.
- إرسالها إلى weather-core عبر:
  - `POST /api/weather/api/v1/weather/ingest`

## 4. AI Layer – agent-ai

خدمة:
- `agent-ai`

وظيفتها:
- جمع سياق الحقل من:
  - geo-core, imagery-core, weather-core, soil-core, analytics-core, alerts-core
- تمرير السياق إلى نموذج LLM (مثل GPT) لصياغة إجابة ذكية.

Endpoints:
- `POST /api/v1/agent/field-advice`
- يتم استدعاؤها عبر:
  - `gateway-edge` من خلال المسار:
  - `POST /api/agent/api/v1/agent/field-advice`

## 5. API Gateway – gateway-edge

مسؤول عن:
- توجيه كل طلبات الواجهة إلى الخدمات المناسبة.
- مسارات مثل:
  - `/api/geo/...`
  - `/api/imagery/...`
  - `/api/weather/...`
  - `/api/timeline/...`
  - `/api/agent/...`

يمتلك SERVICE_MAP لتحديد عناوين الخدمات داخل الكلاستر.

## 6. Frontend (web – Next.js Farmer Dashboard)

الميزات الحالية:

- صفحة Tenant:
  - قائمة الحقول
  - عرض Health + Alerts + Timeline مختصر
  - MapView (Leaflet) لكل حقل (Marker + BBox).

- صفحة Field Detail:
  - Tabs: Overview / NDVI & Soil / Weather / Alerts / AI.
  - عرض:
    - Area, Location, Health
    - خريطة
    - TimelineChart (NDVI/ETo/Rain)
    - قائمة Alerts
    - AgentChat للتفاعل مع agent-ai

الواجهة مبنية بحيث يمكن توسيعها بسهولة لعرض:

- طبقات NDVI Raster في الخريطة.
- Charts متقدمة للطقس.
- مقارنة بين فترات زمنية مختلفة لكل حقل.

## 7. التشغيل والنشر

### Docker Compose (بيئة تطوير)

- ملف `docker-compose.enterprise.yml` يقوم بتشغيل:
  - جميع core services
  - ingestors
  - gateway-edge
  - agent-ai
  - قواعد البيانات (Postgres + PostGIS)
  - web (عند تشغيل npm dev)


### Helm/Kubernetes (بيئة إنتاج)

- تم تجهيز مخططات Helm (charts) لنشر المنصة على Kubernetes:
  - deployment + service لكل microservice
  - تكامل مع ingress controller لتمرير الترافيك إلى gateway-edge
  - إمكانية تفعيل autoscaling و resource limits.

## 8. ملاحظات للتطوير المستقبلي

- ربط ndvi-processor مع imagery-core بشكل أوتوماتيكي:
  - عند نجاح ingestion لمشهد جديد، تشغيل Job لحساب NDVI وتحديث timeline.
- إضافة ML models في analytics-core للمهام:
  - Yield Prediction
  - Disease Risk
  - Irrigation Optimization
- تفعيل Tracing (OpenTelemetry) عبر جميع الخدمات.
- إضافة طبقات Raster في الواجهة (Leaflet/MapLibre) للـ NDVI والخرائط الأخرى.

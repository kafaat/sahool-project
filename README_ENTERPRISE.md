# Sahool v280 - Enterprise Edition (Docker + Helm + Monitoring)

## 1. التشغيل محليًا عبر Docker

```bash
cp .env.example .env
docker compose -f docker-compose.enterprise.yml build
docker compose -f docker-compose.enterprise.yml up
```

## 2. النشر على Kubernetes عبر Helm

### 2.1 إعداد القيم

لبيئة تجريبية / تطوير:

```bash
cd helm/sahool-platform
helm install sahool-platform . -n sahool --create-namespace
```

لبيئة إنتاج Production باستخدام ملف `values.production.yaml`:

```bash
cd helm/sahool-platform
helm install sahool-platform . \
  -f values.production.yaml \
  -n sahool --create-namespace
```

### 2.2 ServiceMonitor للمراقبة (Prometheus)

تم إضافة `ServiceMonitor` اختياري في:

- `templates/servicemonitor.yaml`

يتم تفعيله عبر القيم:

```yaml
monitoring:
  enabled: true
  prometheus:
    serviceMonitor:
      enabled: true
      namespace: "monitoring"
```

### 2.3 Ingress جاهز لـ NGINX

يتم إنشاء Ingress باسم:

- `sahool-gateway-ingress`

ويربط:

- الدومين: `ingress.host` من `values.yaml`
- بالخدمة: `sahool-gateway-edge` على المنفذ 9000

تحتاج لإضافة TLS Secret باسم:

```bash
kubectl create secret tls sahool-gateway-tls \
  -n sahool \
  --cert=fullchain.pem \
  --key=privkey.pem
```

وبذلك تحصل على نشر كامل للمشروع (v280) بمستوى Enterprise جاهز للمراقبة والتوسّع.


## 3. المراقبة Monitoring و الـ Alerts

- راجع `helm/sahool-platform/MONITORING_README.md` لمزيد من التفاصيل حول:
  - ServiceMonitor (Prometheus)
  - PrometheusRule (Alerts)
  - Grafana Dashboards

## 4. اختبارات الـ Core (Pytest)

تم إضافة اختبارات بسيطة لكل خدمة أساسية (core services) للتحقق من صحة مسار `/health` لكل خدمة.

### تشغيل الاختبارات لخدمة معيّنة

مثال: geo-core

```bash
cd multi-repo/geo-core/multi-repo/geo-core
pytest -q
```

مثال: weather-core

```bash
cd multi-repo/weather-core/multi-repo/weather-core
pytest -q
```

مثال: gateway-edge

```bash
cd multi-repo/gateway-edge/multi-repo/gateway-edge
pytest -q
```

> الاختبارات تستخدم FastAPI TestClient وتتأكد أن `/health` ترجع `status: "ok"`، وهذا يضمن أن الكود الأساسي لكل خدمة (core) يعمل بدون أخطاء استيراد أو تهيئة.

## 5. واجهة الويب Farmer Dashboard (Next.js)

تم إضافة مشروع واجهة ويب تحت المجلد:

```bash
web/
```

### 5.1 التشغيل محليًا

من داخل مجلد `web`:

```bash
cd web
npm install
npm run dev
```

ثم افتح المتصفح على:

```text
http://localhost:3000
```

> تأكد أن الـ API (gateway-edge) شغّال على `http://localhost:9000`  
> ويمكنك تغيير عنوان الـ API عبر المتغير:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:9000
```

داخل ملف `.env.local` في مجلد `web`.

### 5.2 ماذا تعرض الواجهة؟

- شاشة رئيسية بسيطة مع رابط إلى:
  - `/tenant/1` على سبيل المثال.
- صفحة Tenant Dashboard:
  - قائمة الحقول (Fields) من `GET /api/geo/fields?tenant_id=...`
  - لوحة Overview للحقل مع:
    - Health Score من `GET /api/analytics/field/{id}/health`
    - Recent Alerts من `GET /api/alerts/field/{id}`
    - Timeline (placeholder) من `GET /api/timeline/field/{id}` (عبر gateway لاحقاً)

يمكنك توسعة الواجهة لاحقًا لإضافة خريطة، Charts، وواجهات تفصيلية لكل خدمة.

### 5.3 تطوير الواجهة (Charts + Map Placeholder)

تم إضافة:

- مكوّن `TimelineChart`:
  - يعرض خطين بسيطين (NDVI و ETo) باستخدام SVG فقط.
  - يعتمد على بيانات `timeline` القادمة من API.

- مكوّن `MapPlaceholder`:
  - يعرض إحداثيات الحقل (centroid).
  - جاهز لاحقًا لاستبداله بخريطة حقيقية (MapLibre / Leaflet) مع حدود الحقل وطبقات NDVI.

يمكنك لاحقًا استبدال الـ Placeholder بدمج مكتبة خرائط، بدون الحاجة لتعديل الـ backend.

## 6. Timeline Core + Agent-AI Integration

### 6.1 Timeline Core

تم تفعيل خدمة `timeline-core` فعلياً مع مسار:

- `GET /api/v1/timeline/field/{field_id}?tenant_id=...`

وتقوم الخدمة حالياً ببناء خط زمني بسيط بالاعتماد على:

- `weather-core` عبر `gateway-edge` للحصول على `eto_mm` و `rain_mm` و `timestamp`
- تحويل النتائج إلى شكل `timeline` يمكن للواجهة استهلاكه مباشرة.

يمكن استدعاء الخدمة من خلال البوابة:

```text
GET /api/timeline/api/v1/timeline/field/{field_id}?tenant_id=...
```

### 6.2 Agent-AI Field Assistant

تم ربط خدمة `agent-ai` عبر `gateway-edge`:

- Endpoint داخلي في agent-ai:
  - `POST /api/v1/agent/field-advice`
- عبر البوابة:
  - `POST /api/agent/api/v1/agent/field-advice`

وتم إضافة مكوّن واجهة:

- `components/AgentChat.tsx`

يظهر داخل صفحة:

- `/tenant/[tenantId]`

ويسمح للمستخدم بطرح سؤال عن حقل معيّن، ثم يقوم باستدعاء:

- `agent-ai` عبر `gateway-edge`، ويحصل على:
  - `reply`
  - `priority`
  - `context` (اختياري)

هذا يشكّل أساس واجهة "مساعد المزارع الذكي" المعتمدة على بيانات الحقول والطقس والتربة.

### 7. خريطة حقيقية في واجهة المزارع (Leaflet)

تم إضافة مكوّن:

- `web/components/MapView.tsx`

يعتمد على:

- `leaflet`
- `react-leaflet`
- طبقة أساس من OpenStreetMap

ويقوم بـ:

- عرض موقع الحقل اعتماداً على `centroid_lat` و `centroid_lon` فقط (Marker)
- إعطاء مركز افتراضي (مثال: اليمن) إذا لا توجد إحداثيات.

يمكن لاحقاً استبدال الـ Marker برسم حدود الحقل (Polygon) عندما يتم إرجاع الـ geometry من `geo-core`.

## 8. خدمات Ingestion (أقمار صناعية، NDVI، طقس)

### 8.1 Satellite Ingestor (CDSE Scaffold)

تم توسيع خدمة `satellite-ingestor` لتشمل:

- `app/services/cdse_client.py`:
  - عميل مبسط لـ Copernicus Data Space Ecosystem عبر OData.

- `app/services/ingest_service.py`:
  - `ingest_field_sentinel2(field_id, tenant_id, ...)`:
    - يجلب AOI للحقل من `geo-core` عبر `gateway-edge` (centroid حالياً).
    - يستدعي CDSE للبحث عن مشاهد Sentinel-2 خلال فترة زمنية.
    - يحاول إبلاغ `imagery-core` عبر مسار مبدئي:
      - `/api/imagery/api/v1/imagery/ingest`
    - هذه الواجهة تحتاج أن تكمّل فعلياً داخل imagery-core لكي تصبح عملية التسجيل حقيقية.

- `app/api/routes.py`:
  - `POST /api/v1/ingest/field/{field_id}?tenant_id=...`

> الكود يعكس خط CDSE الحقيقي (OData)، لكنه قد يحتاج تعديلات بسيطة عند ربطه فعلياً بالبيئة الإنتاجية واعتماد الفلاتر النهائية.

### 8.2 NDVI Processor

تم إضافة خدمة حقيقية لحساب NDVI داخل `ndvi-processor`:

- `app/services/ndvi_service.py`:
  - `compute_ndvi_from_tif(path, red_band=3, nir_band=4)`:
    - يقرأ TIF باستخدام rasterio.
    - يحسب NDVI = (NIR - RED) / (NIR + RED) مع تجنّب القسمة على صفر.
    - يرجع إحصائيات:
      - mean / min / max.

- `app/api/routes.py`:
  - `POST /api/v1/ndvi/compute?path=/data/example.tif`

يمكن لاحقاً:

- ربط هذه الخدمة مع MinIO:
  - تنزيل البلاطة أولاً إلى مسار محلي ثم تمرير المسار للدالة.
- تخزين النتائج في imagery-core كنقاط على الخط الزمني.

### 8.3 Weather Ingestor (Open-Meteo Scaffold)

تم توسيع خدمة `weather-ingestor`:

- `app/services/ingest_service.py`:
  - `ingest_field_weather(field_id, tenant_id)`:
    - يجلب centroid الحقل من geo-core عبر gateway.
    - يستدعي Open-Meteo لثلاثة أيام قادمة (hourly temperature & precipitation).
    - يبني قائمة `WeatherPoint` (timestamp, rain_mm, temp_c, eto_mm=None).
    - يحاول إرسال هذه النقاط إلى مسار M2M داخل weather-core (يحتاج استكمال):

      - `/api/weather/api/v1/weather/ingest`

- `app/api/routes.py`:
  - `POST /api/v1/ingest/field/{field_id}?tenant_id=...`

> هذه الخدمات تعطيك هيكل واضح وخط أنابيب منطقي، لكن يلزمك استكمال المسارات داخل imagery-core و weather-core لتخزين النتائج فعلياً في قاعدة البيانات.

### 8.4 ربط الـ Ingestors مع الـ Core Services

#### Imagery Ingest

تم إضافة مسار حقيقي داخل `imagery-core`:

- `POST /api/v1/imagery/ingest`

يستقبل `SatelliteIngestRequest` ويقوم بـ:

- إنشاء سجل جديد في جدول `satellite_images`:
  - `tenant_id`
  - `field_id`
  - `scene_id` (external_id)
  - `product_name`
  - `timestamp` (ingestion_ts)
  - `cloudcover` (افتراضي 0 لو غير موجود)
  - `ndvi_path` / `raw_zip` (يمكن تعبئتها لاحقاً بعد التحميل والمعالجة)

هذا المسار هو الذي تستدعيه خدمة `satellite-ingestor` عبر `gateway-edge` بعد قراءة مشاهد Sentinel-2 من CDSE.

#### Weather Ingest

تم إضافة مسار حقيقي داخل `weather-core`:

- `POST /api/v1/weather/ingest`

يستقبل `WeatherIngestRequest` ويقوم بـ:

- إدخال مجموعة من `WeatherForecast` rows في قاعدة البيانات لكل نقطة زمنية.
- يمكن بعد ذلك استرجاع هذه النقاط عبر المسار السابق:
  - `GET /api/v1/weather/forecast?tenant_id=...&field_id=...`

هذا المسار هو الذي تستدعيه خدمة `weather-ingestor` بعد جلب بيانات Open-Meteo لكل حقل.

## 9. تحسينات Core احترافية (Observability & Service Metadata)

تم إضافة نقطة معلومات موحّدة لكل خدمة Core:

- `geo-core`
- `imagery-core`
- `weather-core`
- `soil-core`
- `analytics-core`
- `alerts-core`
- `timeline-core`

كل خدمة تعرض الآن:

- `GET /health`
  - حالة بسيطة (status + service)
- `GET /info`
  - `service`: اسم الخدمة
  - `version`: رقم الإصدار (من FastAPI app)
  - `environment`: من متغير البيئة `SAHOOL_ENV` (افتراضي `local`)

هذا يسهل:

- المراقبة (Monitoring) عبر Prometheus/Grafana أو أي APM آخر.
- فحص الإصدارات في بيئات متعددة (dev / staging / prod).
- عمليات الـ debugging في الكلاستر عند وجود أكثر من نسخة من نفس الخدمة.

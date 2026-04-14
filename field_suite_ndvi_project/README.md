# Field Suite NDVI - نظام تحليل صحة المحاصيل

## المميزات
- تحليل NDVI من صور Sentinel-2
- اكتشاف تلقائي لحدود الحقول
- تقسيم الحقول إلى مناطق بناءً على صحة النبات
- خريطة تفاعلية مع MapLibre GL
- دعم قاعدة بيانات PostGIS

## التشغيل

### باستخدام Docker
```bash
cd field_suite_ndvi_project
docker-compose up -d
```

### الروابط
- **الواجهة**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Nginx Proxy**: http://localhost:8080

## API Endpoints

| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/` | فحص الصحة |
| GET | `/fields/` | قائمة الحقول |
| POST | `/fields/ndvi-detect` | اكتشاف NDVI |
| GET | `/fields/{id}/zones` | مناطق الحقل |
| POST | `/ndvi/heatmap` | خريطة حرارية |

## متطلبات الملفات
- B04 (Red Band): ملف .tif أو .jp2
- B08 (NIR Band): ملف .tif أو .jp2

يمكن تحميلها من Copernicus Open Access Hub

# سهول اليمن - مرجع API
# Sahool Yemen - API Reference

## نظرة عامة | Overview

منصة سهول اليمن توفر مجموعة من واجهات برمجة التطبيقات (APIs) لإدارة العمليات الزراعية في اليمن.

## الخدمات المتاحة | Available Services

| Service | Port | Base URL | Description |
|---------|------|----------|-------------|
| Field Suite API | 8000 | `/api/v1` | الخدمة الرئيسية |
| Weather Core | 8003 | `/api/v1/weather` | بيانات الطقس |
| Geo Core | 8005 | `/api/v1/geo` | الخدمات الجغرافية |
| Imagery Core | 8006 | `/api/v1/imagery` | معالجة الصور |
| Analytics Core | 8007 | `/api/v1/analytics` | التحليلات |

## المصادقة | Authentication

### JWT Token

```http
Authorization: Bearer <your-jwt-token>
```

### الحصول على Token | Get Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## الطقس | Weather API

### الطقس الحالي | Current Weather

```http
GET /api/v1/weather/regions/{region_id}
```

**Parameters:**
- `region_id` (path): معرف المحافظة (1-20)

**Response:**
```json
{
  "region_id": 1,
  "date": "2024-01-15",
  "temperature": 25.5,
  "tmax": 28.0,
  "tmin": 18.0,
  "humidity": 45.0,
  "rainfall": 0.0,
  "wind_speed": 12.5,
  "source": "محطة صنعاء"
}
```

### التوقعات | Weather Forecast

```http
GET /api/v1/weather/regions/{region_id}/forecast?days=5
```

**Parameters:**
- `region_id` (path): معرف المحافظة
- `days` (query): عدد أيام التوقع (1-14)

### التنبيهات | Weather Alerts

```http
GET /api/v1/weather/alerts
```

---

## الجغرافيا | Geo API

### حساب المساحة | Calculate Area

```http
POST /api/v1/geo/compute-area
Content-Type: application/json

{
  "type": "Polygon",
  "coordinates": [[[44.0, 15.0], [44.1, 15.0], [44.1, 15.1], [44.0, 15.1], [44.0, 15.0]]]
}
```

**Response:**
```json
{
  "area_ha": 5.75,
  "area_m2": 57500.0,
  "perimeter_m": 980.5
}
```

### الارتفاع | Elevation

```http
GET /api/v1/geo/elevation?lat=15.3&lon=44.2
```

### المسافة | Distance

```http
GET /api/v1/geo/distance?lat1=15.3&lon1=44.2&lat2=13.5&lon2=44.0
```

### معلومات المنطقة | Zone Info

```http
GET /api/v1/geo/zone-info?lat=15.3&lon=44.2
```

---

## الحقول | Fields API

### إنشاء حقل | Create Field

```http
POST /api/v1/fields
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "حقل القمح الشمالي",
  "region_id": 1,
  "area_hectares": 5.5,
  "crop_type": "قمح",
  "geometry": {
    "type": "Polygon",
    "coordinates": [...]
  }
}
```

### قائمة الحقول | List Fields

```http
GET /api/v1/fields?page=1&limit=20
```

### تفاصيل حقل | Get Field

```http
GET /api/v1/fields/{field_id}
```

### تحليل NDVI

```http
GET /api/v1/fields/{field_id}/ndvi?date=2024-01-15
```

---

## التحليلات | Analytics API

### ملخص الإنتاج | Yield Summary

```http
GET /api/v1/analytics/yield-summary?year=2024
```

### تقرير موسمي | Seasonal Report

```http
GET /api/v1/analytics/seasonal-report?season=winter&year=2024
```

---

## أكواد الخطأ | Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | طلب غير صالح |
| 401 | Unauthorized | غير مصرح - تحقق من التوكن |
| 403 | Forbidden | محظور - لا تملك الصلاحية |
| 404 | Not Found | غير موجود |
| 422 | Validation Error | خطأ في التحقق من البيانات |
| 429 | Too Many Requests | تجاوز حد الطلبات |
| 500 | Server Error | خطأ في الخادم |

---

## المحافظات اليمنية | Yemen Governorates

| ID | Name (AR) | Name (EN) |
|----|-----------|-----------|
| 1 | صنعاء | Sana'a |
| 2 | عدن | Aden |
| 3 | تعز | Taiz |
| 4 | الحديدة | Hudaydah |
| 5 | إب | Ibb |
| 6 | ذمار | Dhamar |
| 7 | حضرموت | Hadhramaut |
| 8 | المهرة | Al Mahrah |
| 9 | شبوة | Shabwah |
| 10 | أبين | Abyan |
| 11 | لحج | Lahij |
| 12 | الضالع | Ad Dali |
| 13 | البيضاء | Al Bayda |
| 14 | مأرب | Ma'rib |
| 15 | الجوف | Al Jawf |
| 16 | صعدة | Sa'dah |
| 17 | عمران | Amran |
| 18 | حجة | Hajjah |
| 19 | المحويت | Al Mahwit |
| 20 | ريمة | Raymah |

---

## Swagger UI

كل خدمة توفر واجهة Swagger للتوثيق التفاعلي:

- **Field Suite API**: http://localhost:8000/docs
- **Weather Core**: http://localhost:8003/docs
- **Geo Core**: http://localhost:8005/docs
- **Analytics Core**: http://localhost:8007/docs

## ReDoc

للتوثيق المفصل:

- **Field Suite API**: http://localhost:8000/redoc
- **Weather Core**: http://localhost:8003/redoc

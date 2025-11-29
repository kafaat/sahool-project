# geo-core

خدمة **Geo Core** لإدارة الحقول (Fields) وحدودها باستخدام **PostGIS**.

## مميزات

- تخزين الحدود كـ MULTIPOLYGON (SRID 4326) في PostGIS.
- حساب المساحة بالهكتار (ha) عبر `shapely + pyproj`.
- حفظ مركز الحقل (centroid) كنقطة (lat/lon).
- واجهات برمجية لإدارة الحقول:

### Endpoints

- `GET  /health`
- `GET  /api/v1/fields?tenant_id=1`
- `POST /api/v1/fields`
- `GET  /api/v1/fields/{field_id}?tenant_id=1`
- `PUT  /api/v1/fields/{field_id}?tenant_id=1`
- `DELETE /api/v1/fields/{field_id}?tenant_id=1`

### مثال طلب إنشاء حقل

```json
{
  "tenant_id": 1,
  "name": "Field A",
  "crop": "Wheat",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [43.0, 16.0],
        [43.001, 16.0],
        [43.001, 16.001],
        [43.0, 16.001],
        [43.0, 16.0]
      ]
    ]
  }
}
```

## تشغيل محليًا

```bash
cd multi-repo/geo-core
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/sahool"

uvicorn app.main:app --reload --port 8005
```

> تأكد أن قاعدة البيانات فيها **PostGIS extension**:
>
> ```sql
> CREATE EXTENSION IF NOT EXISTS postgis;
> ```
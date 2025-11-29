# soil-core

خدمة **Soil Core** لإدارة عينات التربة ومؤشرات خصوبة/ملوحة التربة.

## Endpoints

- `GET  /health`
- `POST /api/v1/soil/samples`
- `GET  /api/v1/soil/samples?tenant_id=1&field_id=10`
- `GET  /api/v1/soil/fields/{field_id}/summary?tenant_id=1`

## مثال طلب إنشاء عينة

```json
{
  "tenant_id": 1,
  "field_id": 10,
  "sample_date": "2025-11-01",
  "depth_cm": 30,
  "ph": 7.8,
  "ec_ds_m": 3.2,
  "moisture_pct": 18.0,
  "organic_matter_pct": 1.2,
  "lab_ref": "LAB-001",
  "notes": "عينة من منتصف الحقل"
}
```
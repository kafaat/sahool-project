# alerts-core

خدمة **Alerts Core** لإدارة التنبيهات الزراعية.

## Endpoints

- `GET  /health`
- `POST /api/v1/alerts`
- `GET  /api/v1/alerts/recent?tenant_id=1&hours=72`
- `GET  /api/v1/alerts/field/{field_id}?tenant_id=1`
- `POST /api/v1/alerts/{alert_id}/read?tenant_id=1`
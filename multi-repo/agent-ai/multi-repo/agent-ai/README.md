# agent-ai

خدمة **Agent AI** بسيطة تقوم بـ:
- استدعاء الخدمات عبر gateway-edge
- جمع بيانات الحقل (تربة + طقس + صور + تنبيهات)
- تطبيق قواعد منطقية بسيطة
- إرجاع توصيات وتحذيرات نصية

## Endpoint

POST `/api/v1/agent/field-advice`

```json
{
  "tenant_id": 1,
  "field_id": 10,
  "message": "أريد تقييم حالة الحقل"
}
```
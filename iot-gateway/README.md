# 🌐 IoT Gateway Service

خدمة بوابة إنترنت الأشياء لمنصة Sahool الزراعية

## 📋 نظرة عامة

IoT Gateway هي خدمة مركزية لإدارة الاتصال مع أجهزة الاستشعار الزراعية وأجهزة IoT في الحقول. تدعم الخدمة بروتوكول MQTT للاتصال الموثوق والفعال مع الأجهزة.

## 🎯 الميزات

### 1. إدارة الأجهزة
- تسجيل وإلغاء تسجيل الأجهزة
- مراقبة حالة الأجهزة (Online/Offline)
- تتبع آخر نشاط للأجهزة
- إدارة البطارية وقوة الإشارة

### 2. MQTT Integration
- الاتصال بـ MQTT Broker
- الاشتراك في Topics متعددة
- معالجة الرسائل الواردة
- نشر الأوامر للأجهزة

### 3. أنواع الحساسات المدعومة
- **حساسات رطوبة التربة** - قياس رطوبة التربة
- **حساسات الحرارة** - قياس درجة الحرارة
- **حساسات الرطوبة الجوية** - قياس الرطوبة النسبية
- **حساسات الضوء** - قياس شدة الإضاءة
- **حساسات pH** - قياس حموضة التربة
- **حساسات EC** - قياس الموصلية الكهربائية

### 4. Real-time Data
- WebSocket للبيانات الفورية
- Broadcast لجميع العملاء المتصلين
- معالجة البيانات في الوقت الفعلي

## 🛠️ التقنيات المستخدمة

- **FastAPI** - إطار عمل الـ API
- **Paho MQTT** - عميل MQTT
- **WebSocket** - للاتصال الفوري
- **Python 3.11+** - لغة البرمجة

## 📦 التثبيت

```bash
cd iot-gateway

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المكتبات
pip install -r requirements.txt
```

## 🚀 التشغيل

### Development Mode

```bash
# تشغيل الخدمة
uvicorn app.main:app --reload --port 8005

# أو باستخدام Python
python -m app.main
```

### Production Mode

```bash
# باستخدام Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8005
```

### Docker

```bash
# بناء الصورة
docker build -t sahool-iot-gateway .

# تشغيل الحاوية
docker run -p 8005:8005 sahool-iot-gateway
```

## 🔧 التكوين

### متغيرات البيئة

```env
# MQTT Broker
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=sahool
MQTT_PASSWORD=your_password

# Database
DATABASE_URL=postgresql://user:pass@localhost/sahool

# API
API_PORT=8005
LOG_LEVEL=INFO
```

## 📡 MQTT Topics

### Topics للاشتراك

```
sahool/sensors/+/data          # بيانات الحساسات
sahool/devices/+/status        # حالة الأجهزة
sahool/commands/+              # الأوامر
```

### Topics للنشر

```
sahool/commands/{device_id}    # أوامر للأجهزة
sahool/config/{device_id}      # تكوين الأجهزة
```

## 🔌 API Endpoints

### Device Management

```http
GET    /api/v1/devices                 # قائمة جميع الأجهزة
POST   /api/v1/devices                 # تسجيل جهاز جديد
GET    /api/v1/devices/{device_id}     # تفاصيل جهاز
PUT    /api/v1/devices/{device_id}     # تحديث جهاز
DELETE /api/v1/devices/{device_id}     # حذف جهاز
```

### Sensor Data

```http
GET    /api/v1/sensors/data            # آخر بيانات الحساسات
GET    /api/v1/sensors/data/history    # سجل البيانات
GET    /api/v1/sensors/{device_id}/latest  # آخر قراءة لجهاز
```

### Field Devices

```http
GET    /api/v1/fields/{field_id}/devices  # أجهزة حقل معين
GET    /api/v1/fields/{field_id}/sensors  # حساسات حقل معين
```

### WebSocket

```
ws://localhost:8005/ws/sensors         # بيانات فورية
```

## 📊 تنسيق البيانات

### Sensor Data Message

```json
{
  "device_id": "sensor_001",
  "device_type": "soil_moisture",
  "field_id": 123,
  "timestamp": "2024-11-30T10:30:00Z",
  "data": {
    "moisture": 45.5,
    "temperature": 22.3,
    "battery": 85,
    "signal": -65
  },
  "location": {
    "lat": 24.7136,
    "lon": 46.6753
  }
}
```

### Device Status Message

```json
{
  "device_id": "sensor_001",
  "status": "online",
  "battery_level": 85,
  "signal_strength": -65,
  "firmware_version": "1.2.3",
  "timestamp": "2024-11-30T10:30:00Z"
}
```

## 🔐 الأمان

### Authentication
- JWT tokens للـ API endpoints
- MQTT username/password
- TLS/SSL للاتصالات الآمنة

### Authorization
- التحقق من صلاحيات الأجهزة
- تقييد الوصول حسب الـ Tenant
- Audit logging لجميع العمليات

## 🧪 الاختبار

```bash
# تشغيل الاختبارات
pytest

# مع Coverage
pytest --cov=app --cov-report=html

# اختبار MQTT
python tests/test_mqtt_client.py
```

## 📝 أمثلة الاستخدام

### تسجيل جهاز جديد

```bash
curl -X POST http://localhost:8005/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor_001",
    "device_type": "soil_moisture",
    "field_id": 123,
    "location": {
      "lat": 24.7136,
      "lon": 46.6753
    }
  }'
```

### نشر بيانات حساس (MQTT)

```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883, 60)

data = {
    "moisture": 45.5,
    "temperature": 22.3,
    "battery": 85
}

client.publish("sahool/sensors/sensor_001/data", json.dumps(data))
```

### الاتصال بـ WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8005/ws/sensors');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Sensor data:', data);
};
```

## 🔄 Integration

### مع Platform Core
```python
# إرسال البيانات إلى Platform Core
async def send_to_platform(sensor_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://platform-core:8001/api/v1/sensors/data",
            json=sensor_data
        )
```

### مع Analytics Core
```python
# إرسال للتحليل
async def send_to_analytics(sensor_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://analytics-core:8003/api/v1/analytics/ingest",
            json=sensor_data
        )
```

## 🐛 استكشاف الأخطاء

### المشكلة: "Cannot connect to MQTT broker"
**الحل:** 
- تأكد من تشغيل MQTT broker (Mosquitto)
- تحقق من المنفذ والعنوان
- تأكد من بيانات الاعتماد

### المشكلة: "Device not receiving commands"
**الحل:**
- تحقق من اشتراك الجهاز في Topic الصحيح
- تأكد من تنسيق الرسالة
- راجع logs للأخطاء

### المشكلة: "WebSocket connection drops"
**الحل:**
- زيادة timeout
- تحقق من استقرار الشبكة
- استخدام reconnection logic

## 📚 الموارد

- [MQTT Protocol](https://mqtt.org/)
- [Paho MQTT Client](https://www.eclipse.org/paho/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)

## 🚀 الميزات القادمة

- [ ] دعم LoRaWAN
- [ ] دعم CoAP protocol
- [ ] Device firmware updates OTA
- [ ] Advanced alerting rules
- [ ] ML-based anomaly detection
- [ ] Multi-broker support
- [ ] Device grouping
- [ ] Batch data processing

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- GitHub Issues: https://github.com/kafaat/sahool-project/issues
- Email: support@sahool.com

## 📄 الترخيص

MIT License - انظر ملف LICENSE للتفاصيل

# platform-core

نواة المنصة (Platform Core) وتحتوي على:

- الإعدادات العامة (config)
- الاتصال بقاعدة البيانات
- النماذج الأساسية (Tenant, User)
- نظام تسجيل الدخول (JWT بسيط)
- واجهات:
  - POST /api/v1/tenants
  - POST /api/v1/auth/token
  - GET  /api/v1/users/me
- نقطة فحص الصحة /health

## التشغيل محلياً

```bash
cd multi-repo/platform-core
python -m venv .venv
source .venv/bin/activate  # في ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sahool"
uvicorn app.main:app --reload --port 9000
```

## باستخدام Docker

```bash
cd multi-repo/platform-core
docker build -t platform-core:latest .
docker run -p 9000:9000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/sahool" \
  platform-core:latest
```
# 💰 دليل نظام تتبع تكلفة LLM - Cost Tracking System

## نظرة عامة | Overview

نظام شامل لتتبع ومراقبة تكاليف استخدام LLM (OpenAI, Anthropic) لحماية من التكاليف العالية غير المتوقعة.

### ⚠️ المشكلة

بدون مراقبة التكلفة:
- ❌ قد تصل التكاليف إلى **$500/يوم أو أكثر!**
- ❌ لا رؤية للاستخدام الفعلي
- ❌ صعوبة في التحكم بالميزانية
- ❌ مفاجآت في الفاتورة نهاية الشهر

### ✅ الحل

نظام تتبع شامل يوفر:
- ✅ تتبع دقيق للتكلفة بناءً على الاستخدام الفعلي
- ✅ حدود يومية وشهرية قابلة للتخصيص
- ✅ تنبيهات عند 50%, 75%, 90% من الحد
- ✅ منع الطلبات عند تجاوز الحد
- ✅ تقارير تفصيلية ومراقبة في الوقت الفعلي
- ✅ تتبع لكل tenant/user
- ✅ دعم جميع نماذج OpenAI و Anthropic

---

## 📋 المكونات الأساسية

### 1. **Cost Tracker** (`cost_tracker.py`)

النواة الأساسية للنظام - يتتبع ويحسب التكاليف.

```python
from app.services.cost_tracker import get_cost_tracker

# Initialize
tracker = get_cost_tracker(
    max_daily_cost=100.0,    # $100/day limit
    max_monthly_cost=2000.0   # $2000/month limit
)

# Estimate cost before request
estimated_cost = tracker.estimate_cost(
    model="gpt-4-turbo-preview",
    input_tokens=500,
    output_tokens=1000
)

# Check if within limits
check = tracker.check_limits(estimated_cost)
if not check["allowed"]:
    raise Exception(check["message"])

# Record actual usage
tracker.record_usage(
    model="gpt-4-turbo-preview",
    input_tokens=500,
    output_tokens=1000,
    user_id="user123",
    tenant_id="tenant456"
)

# Get summary
summary = tracker.get_daily_summary()
print(f"Today's cost: ${summary.total_cost:.2f}")
```

### 2. **Cost Middleware** (`cost_middleware.py`)

Middleware لـ FastAPI - يتحقق من الحدود تلقائياً قبل كل طلب.

```python
from fastapi import FastAPI
from app.middleware.cost_middleware import CostTrackingMiddleware

app = FastAPI()
app.add_middleware(CostTrackingMiddleware)

# الآن كل طلب إلى /agent/* سيتم التحقق من تكلفته تلقائياً!
```

### 3. **Cost Monitoring API** (`cost_monitoring.py`)

Endpoints للمراقبة والإدارة:

- `GET /api/v2/cost/status` - الوضع الحالي
- `GET /api/v2/cost/summary/daily` - ملخص يومي
- `GET /api/v2/cost/summary/monthly` - ملخص شهري
- `GET /api/v2/cost/estimate` - تقدير تكلفة طلب
- `POST /api/v2/cost/limits/update` - تحديث الحدود
- `POST /api/v2/cost/reset/daily` - إعادة تعيين يدوي

---

## 💸 أسعار النماذج المدعومة

### OpenAI Models

| Model | Input ($/1K tokens) | Output ($/1K tokens) | Use Case |
|-------|---------------------|----------------------|----------|
| **GPT-4 Turbo** | $0.01 | $0.03 | High quality, complex tasks |
| **GPT-4** | $0.03 | $0.06 | Advanced reasoning |
| **GPT-4 32K** | $0.06 | $0.12 | Long context |
| **GPT-3.5 Turbo** | $0.0015 | $0.002 | Fast, cost-effective ✅ |
| **GPT-3.5 16K** | $0.003 | $0.004 | Medium context |

### Anthropic Claude Models

| Model | Input ($/1K tokens) | Output ($/1K tokens) | Use Case |
|-------|---------------------|----------------------|----------|
| **Claude 3 Opus** | $0.015 | $0.075 | Highest intelligence |
| **Claude 3 Sonnet** | $0.003 | $0.015 | Balanced ✅ |
| **Claude 3 Haiku** | $0.00025 | $0.00125 | Fastest, cheapest ✅ |
| **Claude 2.1** | $0.008 | $0.024 | Previous gen |

### 💡 توصيات الاختيار

**للإنتاج (Production):**
- 🟢 GPT-3.5 Turbo - سريع ورخيص
- 🟢 Claude 3 Haiku - أرخص خيار

**للجودة العالية:**
- 🟡 Claude 3 Sonnet - توازن ممتاز
- 🟡 GPT-4 Turbo - أداء قوي

**للمهام المعقدة فقط:**
- 🔴 GPT-4 / Claude 3 Opus - مكلف!

---

## 🚀 التثبيت والإعداد

### 1. تثبيت المتطلبات

```bash
# الحزم مثبتة بالفعل في المشروع
pip install fastapi redis pydantic
```

### 2. تكوين المتغيرات البيئية

```bash
# .env
MAX_DAILY_LLM_COST=100.0      # $100/day
MAX_MONTHLY_LLM_COST=2000.0   # $2000/month
LLM_PROVIDER=openai            # or anthropic
LLM_MODEL=gpt-3.5-turbo       # or claude-3-sonnet-20240229

# Optional: Redis for persistence
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. دمج في التطبيق

**الطريقة السهلة - استخدام التطبيق الجاهز:**

```bash
cd multi-repo/agent-ai
python app/main_with_cost_tracking.py
```

**الطريقة المخصصة - دمج في تطبيق موجود:**

```python
from fastapi import FastAPI
from app.middleware.cost_middleware import CostTrackingMiddleware
from app.routers.cost_monitoring import router as cost_router
from app.services.cost_tracker import get_cost_tracker

app = FastAPI()

# Add middleware
app.add_middleware(CostTrackingMiddleware)

# Add monitoring endpoints
app.include_router(cost_router)

# Initialize tracker
tracker = get_cost_tracker()

# Use in endpoints
@app.post("/agent/chat")
async def chat(message: str):
    # Check cost
    estimated_cost = tracker.estimate_cost_from_text("gpt-3.5-turbo", message)
    check = tracker.check_limits(estimated_cost)

    if not check["allowed"]:
        raise HTTPException(429, check["message"])

    # Process...
    result = await agent.chat(message)

    # Record usage
    tracker.record_usage(
        model="gpt-3.5-turbo",
        input_tokens=len(message) // 4,
        output_tokens=len(result) // 4
    )

    return result
```

---

## 📊 الاستخدام والمراقبة

### مراقبة الوضع الحالي

```bash
# GET /api/v2/cost/status
curl http://localhost:8003/api/v2/cost/status
```

```json
{
  "daily_cost": 12.34,
  "daily_limit": 100.0,
  "daily_percentage": 12.34,
  "daily_remaining": 87.66,
  "monthly_cost": 456.78,
  "monthly_limit": 2000.0,
  "monthly_percentage": 22.84,
  "monthly_remaining": 1543.22,
  "status": "ok",
  "message": "🟢 التكلفة ضمن الحدود الطبيعية"
}
```

### الحصول على ملخص يومي

```bash
curl http://localhost:8003/api/v2/cost/summary/daily
```

```json
{
  "total_cost": 12.34,
  "total_requests": 145,
  "total_input_tokens": 45678,
  "total_output_tokens": 89012,
  "by_model": {
    "gpt-3.5-turbo": 8.50,
    "gpt-4-turbo-preview": 3.84
  },
  "by_provider": {
    "openai": 12.34
  },
  "by_tenant": {
    "tenant_123": 7.20,
    "tenant_456": 5.14
  }
}
```

### تقدير تكلفة طلب

```bash
curl "http://localhost:8003/api/v2/cost/estimate?model=gpt-4-turbo-preview&input_text=قدم%20تحليل%20شامل%20للحقل"
```

```json
{
  "model": "gpt-4-turbo-preview",
  "input_length": 45,
  "estimated_input_tokens": 11,
  "estimated_output_tokens": 16,
  "estimated_cost": 0.00059,
  "formatted_cost": "$0.0006"
}
```

### تحديث الحدود

```bash
curl -X POST "http://localhost:8003/api/v2/cost/limits/update?daily_limit=150.0&monthly_limit=3000.0"
```

---

## 🎯 السيناريوهات الشائعة

### سيناريو 1: بداية اليوم (تكلفة منخفضة)

```
GET /api/v2/cost/status
{
  "daily_cost": 0.0,
  "status": "ok",
  "message": "🟢 التكلفة ضمن الحدود الطبيعية"
}
```

### سيناريو 2: اقتراب من الحد (75%)

```
GET /api/v2/cost/status
{
  "daily_cost": 75.0,
  "daily_percentage": 75.0,
  "status": "warning",
  "message": "🟡 تحذير: التكلفة مرتفعة، راقب الاستخدام"
}
```

**التصرف المطلوب:**
- 📧 إرسال تنبيه للمسؤولين
- 🔍 مراجعة الاستخدام غير الطبيعي
- ⚙️ تفعيل وضع توفير (استخدام نماذج أرخص)

### سيناريو 3: حالة حرجة (90%)

```
GET /api/v2/cost/status
{
  "daily_cost": 92.0,
  "daily_percentage": 92.0,
  "status": "critical",
  "message": "🔴 مستوى التكلفة حرج! اقتربت من الحد الأقصى"
}
```

**التصرف المطلوب:**
- 🚨 تنبيه فوري
- 🔴 تحويل كل الطلبات إلى fallback (rule-based)
- 🛑 إيقاف الخدمات غير الأساسية

### سيناريو 4: تجاوز الحد

```
POST /agent/chat
Response: 429 Too Many Requests
{
  "error": "cost_limit_exceeded",
  "message": "🔴 Daily LLM cost limit reached: $100.00/$100.00. Limit will reset tomorrow.",
  "details": {
    "daily_cost": "$100.00",
    "daily_limit": "$100.00"
  }
}
```

**ماذا يحدث:**
- ❌ الطلب مرفوض
- 🔄 استخدام rule-based fallback
- ⏰ ينتظر حتى منتصف الليل للإعادة

---

## 🛡️ الحماية المتعددة المستويات

### المستوى 1: Middleware (قبل المعالجة)

```python
# يتحقق تلقائياً من كل طلب
CostTrackingMiddleware → check_limits() → allow/deny
```

### المستوى 2: Endpoint (أثناء المعالجة)

```python
@app.post("/agent/chat")
async def chat():
    # تحقق إضافي في الـ endpoint
    check = tracker.check_limits(estimated_cost)
    if not check["allowed"]:
        raise HTTPException(429)
```

### المستوى 3: Agent (داخل المنطق)

```python
# داخل generator.py
if daily_cost > limit * 0.95:
    # استخدام fallback بدلاً من LLM
    return generate_rule_based()
```

---

## 📈 التحليلات والتقارير

### Dashboard بسيط (HTML)

```html
<!DOCTYPE html>
<html>
<head>
    <title>LLM Cost Dashboard</title>
    <script>
        async function loadStatus() {
            const res = await fetch('/api/v2/cost/status');
            const data = await res.json();

            document.getElementById('daily-cost').innerText =
                `$${data.daily_cost.toFixed(2)} / $${data.daily_limit}`;

            document.getElementById('daily-bar').style.width =
                `${data.daily_percentage}%`;
        }

        setInterval(loadStatus, 5000); // Refresh every 5 seconds
    </script>
</head>
<body onload="loadStatus()">
    <h1>💰 LLM Cost Dashboard</h1>

    <div class="metric">
        <h2>Daily Cost</h2>
        <p id="daily-cost">Loading...</p>
        <div class="progress-bar">
            <div id="daily-bar"></div>
        </div>
    </div>
</body>
</html>
```

### تصدير البيانات

```python
# Export daily summary as JSON
summary_json = tracker.export_summary_json()

# Save to file
with open(f"cost_report_{date.today()}.json", "w") as f:
    f.write(summary_json)
```

### تكامل مع أنظمة المراقبة

```python
# Prometheus metrics
from prometheus_client import Gauge

daily_cost_gauge = Gauge('llm_daily_cost_usd', 'Daily LLM cost in USD')
daily_cost_gauge.set(tracker.daily_cost)

# Grafana dashboard
# يمكن عرض المقاييس في Grafana dashboard
```

---

## ⚙️ التكوينات المتقدمة

### حدود لكل Tenant

```python
# يمكن تخصيص حدود لكل tenant
TENANT_LIMITS = {
    "tenant_premium": 500.0,   # Premium plan
    "tenant_basic": 50.0,      # Basic plan
    "tenant_trial": 5.0        # Trial
}

def check_tenant_limit(tenant_id: str, cost: float):
    limit = TENANT_LIMITS.get(tenant_id, 100.0)
    # ... check logic
```

### Fallback تلقائي عند الاقتراب من الحد

```python
def get_model_for_request(cost_percentage: float):
    if cost_percentage > 90:
        return "fallback"  # Rule-based, free
    elif cost_percentage > 75:
        return "claude-3-haiku-20240307"  # Cheapest LLM
    else:
        return "gpt-4-turbo-preview"  # Full quality
```

### تنبيهات Webhook

```python
async def send_alert(threshold: float, cost: float):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        await httpx.post(webhook_url, json={
            "text": f"🚨 LLM Cost Alert: ${cost:.2f} ({threshold}% of limit)"
        })
```

---

## 🧪 الاختبار

```python
import pytest
from app.services.cost_tracker import LLMCostTracker

def test_cost_estimation():
    tracker = LLMCostTracker(max_daily_cost=10.0)

    # Test GPT-3.5
    cost = tracker.estimate_cost("gpt-3.5-turbo", 1000, 1000)
    assert 0.003 < cost < 0.004

    # Test GPT-4
    cost = tracker.estimate_cost("gpt-4-turbo-preview", 1000, 1000)
    assert 0.03 < cost < 0.05

def test_limit_enforcement():
    tracker = LLMCostTracker(max_daily_cost=1.0)

    # Record usage close to limit
    tracker.record_usage("gpt-3.5-turbo", 100000, 100000)

    # Next request should be denied
    check = tracker.check_limits(0.1)
    assert not check["allowed"]
    assert "limit" in check["reason"]

def test_daily_reset():
    tracker = LLMCostTracker()
    tracker.daily_cost = 50.0
    tracker.reset_daily_cost()
    assert tracker.daily_cost == 0.0
```

---

## 📉 أمثلة على التوفير

### مثال 1: تطبيق دردشة زراعي

**بدون تتبع التكلفة:**
- 1000 طلب/يوم × GPT-4 ($0.04 per request) = **$40/يوم** = **$1,200/شهر**

**مع تتبع التكلفة + تحسين:**
- 700 طلب GPT-3.5 Turbo ($0.003) = $2.10
- 200 طلب Claude Haiku ($0.001) = $0.20
- 100 طلب Rule-based (free) = $0.00
- **الإجمالي: $2.30/يوم = $69/شهر**
- **التوفير: 94%!** 🎉

### مثال 2: تحليل الحقول

**سيناريو قبل:**
- تحليل 500 حقل/يوم
- استخدام GPT-4 دائماً
- التكلفة: $0.10 per analysis
- **الإجمالي: $50/يوم = $1,500/شهر**

**سيناريو بعد:**
- 100 حقل حرجة → GPT-4 ($10)
- 200 حقل عادية → GPT-3.5 ($1.20)
- 200 حقل بسيطة → Rule-based ($0)
- **الإجمالي: $11.20/يوم = $336/شهر**
- **التوفير: 78%!** 🎉

---

## 🚨 التعامل مع الحالات الطارئة

### حالة 1: تجاوز مفاجئ

**الأعراض:**
- التكلفة اليومية زادت 10x فجأة
- استهلاك غير طبيعي

**التشخيص:**
```bash
# Check by endpoint
GET /api/v2/cost/summary/daily

# إذا endpoint معين مسؤول:
"by_endpoint": {
  "/agent/chat": 90.0,  // ← المشكلة هنا!
  "/agent/analyze": 5.0
}
```

**الحل:**
```python
# إيقاف الendpoint المشكوك فيه مؤقتاً
@app.post("/agent/chat")
async def chat():
    raise HTTPException(503, "Service temporarily disabled")
```

### حالة 2: هجوم DDoS/Abuse

**الأعراض:**
- طلبات كثيرة جداً من tenant واحد

**الحل:**
```python
# Rate limiting per tenant
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.tenant_id)

@app.post("/agent/chat")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def chat():
    ...
```

---

## 📚 الموارد الإضافية

### وثائق API الكاملة

عند تشغيل التطبيق، زر:
- **Swagger UI:** `http://localhost:8003/docs`
- **ReDoc:** `http://localhost:8003/redoc`

### أسعار LLM محدثة

- OpenAI: https://openai.com/pricing
- Anthropic: https://www.anthropic.com/pricing

### أفضل الممارسات

1. **راقب يومياً** - راجع التقارير كل صباح
2. **حدد بواقعية** - ابدأ بحدود منخفضة وزد تدريجياً
3. **استخدم Fallback** - دائماً اجعل rule-based كـ backup
4. **اختبر أولاً** - جرّب النماذج الأرخص قبل الأغلى
5. **حسّن الـ prompts** - prompts أقصر = تكلفة أقل
6. **استخدم caching** - لا تعيد نفس السؤال مرتين

---

## ✅ الخلاصة

### ما تم إنجازه

✅ نظام تتبع تكلفة شامل
✅ دعم جميع نماذج OpenAI و Anthropic
✅ حدود يومية وشهرية
✅ تنبيهات عند 50%, 75%, 90%
✅ Middleware تلقائي
✅ API endpoints للمراقبة
✅ Persistence مع Redis
✅ تقارير تفصيلية
✅ توثيق كامل

### الأثر المتوقع

- 🛡️ **حماية 100%** من التكاليف غير المتوقعة
- 📉 **توفير 70-90%** من التكاليف مع التحسين
- 📊 **رؤية كاملة** للاستخدام
- ⚡ **استجابة سريعة** للمشاكل
- 💰 **ميزانية محكمة** وقابلة للتنبؤ

### التكلفة المتوقعة للمشروع

**تطبيق زراعي متوسط:**
- 500-1000 طلب/يوم
- استخدام ذكي (GPT-3.5 + Haiku + Fallback)
- **التكلفة: $50-100/شهر** ✅

**مقابل $1,500-3,000/شهر بدون تحسين!** ❌

---

**تاريخ الإنشاء:** 2025-12-01
**الإصدار:** v3.2.4
**الحالة:** Production Ready ✅

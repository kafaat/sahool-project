# SAHOOL AGRI INTELLIGENCE - Professional Edition v2.1

نظام الذكاء الزراعي المتكامل - الإصدار الاحترافي

## 🌟 نظرة عامة

SAHOOL هو نظام ذكاء زراعي متكامل مصمم خصيصاً للزراعة في اليمن والجوف. يجمع بين:
- التقويم الفلكي التقليدي (الأنواء)
- تحليل صور الأقمار الصناعية
- الري الذكي
- تحسين المهام بالذكاء الاصطناعي

---

## 🏗️ البنية المعمارية

```
sahool-project/
├── services/
│   ├── astral-engine-v2/          # محرك الفلك الزراعي
│   ├── ndvi-engine-v2/            # محرك تحليل NDVI
│   ├── irrigation-controller-v2/  # نظام الري الذكي
│   ├── task-optimizer-v2/         # محسن المهام (ML)
│   ├── dashboard-pro-v3/          # لوحة التحكم
│   └── intelligence-orchestrator/ # طبقة التكامل
├── libs-shared/
│   └── sahool_shared/
│       └── intelligence/          # المكتبات المشتركة
├── nano_services/                 # الخدمات المصغرة
└── scripts/                       # سكريبتات البناء والاختبار
```

---

## 🌙 1. Astral Agriculture Engine v2.0

محرك الفلك الزراعي المبني على التقويم اليمني التقليدي.

### الميزات:
- **50+ نوء** من الأنواء اليمنية والجوفية
- **توقعات ML** لتأثير الطوالع على المحاصيل
- **توصيات ذكية** للري والزراعة والحصاد

### مثال الاستخدام:
```typescript
import { AstralEngine } from '@sahool/astral-engine';

const engine = new AstralEngine();
const analysis = await engine.getDayAstralData(new Date());

console.log(analysis.moonPhase);      // 'الذراع'
console.log(analysis.compatibility);  // 'excellent'
console.log(analysis.suggestedTasks); // ['الري', 'الزراعة']
```

---

## 🛰️ 2. NDVI Time Series Engine v2.0

محرك تحليل صور الأقمار الصناعية للمراقبة الزراعية.

### الميزات:
- **تحليل NDVI/NDWI/EVI** متعدد المؤشرات
- **اكتشاف Hotspots** للمناطق المشكلة
- **التنبؤ بالإنتاجية** باستخدام ML
- **تحليل الإجهاد المائي**

### مثال الاستخدام:
```typescript
import { NDVITimeSeriesEngine } from '@sahool/ndvi-engine';

const engine = new NDVITimeSeriesEngine();
const analysis = await engine.analyzeTimeSeries(
  'field-001',
  new Date('2025-01-01'),
  new Date('2025-12-01')
);

console.log(analysis.trends.overallTrend);     // 'improving'
console.log(analysis.yieldPrediction);          // { predictedKgPerHectare: 6500, ... }
console.log(analysis.waterStress.stressLevel); // 'low'
```

---

## 💧 3. Smart Irrigation Controller v2.0

نظام التحكم الذكي في الري.

### الميزات:
- **حساب ET** (Penman-Monteith)
- **تكامل IoT** مع مستشعرات التربة
- **توصيات ذكية** بناءً على الطقس والتربة
- **جدولة تلقائية** للري

### مثال الاستخدام:
```typescript
import { SmartIrrigationController } from '@sahool/irrigation-controller';

const controller = new SmartIrrigationController();
const recommendation = await controller.calculateRealTimeIrrigation('field-001');

if (recommendation.action === 'irrigate') {
  console.log(`الري مطلوب: ${recommendation.volume_mm} ملم`);
  console.log(`الوقت الأمثل: ${recommendation.optimal_time}`);
}
```

---

## 🚜 4. Task Optimization Engine v2.0

محسن المهام الزراعية بالذكاء الاصطناعي.

### الميزات:
- **تحسين ML** لترتيب المهام
- **حساب المسارات** GPS
- **توزيع العمال** الذكي
- **مراعاة القيود** (فلكية، طقس، تربة)

### مثال الاستخدام:
```typescript
import { TaskOptimizationEngine } from '@sahool/task-optimizer';

const optimizer = new TaskOptimizationEngine();
const result = await optimizer.optimizeDailyTasks(
  'field-001',
  new Date(),
  workers,
  { weather: {}, astral: {}, soil: {} }
);

console.log(`المهام المحسنة: ${result.tasks.length}`);
console.log(`الكفاءة: ${result.efficiency * 100}%`);
console.log(`الوقت الموفر: ${result.savings.time_saved_minutes} دقيقة`);
```

---

## 🧠 5. Unified Intelligence Orchestrator

طبقة التكامل الذكية التي تجمع كل المحركات.

### الميزات:
- **تكامل شامل** لجميع المحركات
- **Cache ذكي** (Redis)
- **Circuit Breaker** للمرونة
- **توصيات AI** موحدة

### مثال الاستخدام:
```typescript
import { UnifiedIntelligenceOrchestrator } from '@sahool/intelligence-orchestrator';

const orchestrator = new UnifiedIntelligenceOrchestrator({
  redis: { host: 'localhost', port: 6379 }
});

const intelligence = await orchestrator.generateIntelligence(
  'field-001',
  new Date(),
  'user-123'
);

console.log(`Risk Score: ${intelligence.riskScore}`);
console.log(`التوصيات: ${intelligence.recommendations.length}`);
console.log(`التنبيهات: ${intelligence.alerts.length}`);
```

---

## 📊 6. Dashboard Pro v3.0

لوحة التحكم الاحترافية (React).

### الميزات:
- **عرض الحالة الفلكية**
- **خريطة Hotspots**
- **جدول الري**
- **توصيات AI**
- **تنبيهات ذكية**

---

## 🚀 التثبيت والتشغيل

### المتطلبات:
- Node.js 18+
- PostgreSQL 14+ (مع PostGIS)
- Redis 7+
- Docker (اختياري)

### التثبيت:
```bash
# استنساخ المشروع
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project

# تثبيت التبعيات
npm install

# بناء الأنظمة
chmod +x scripts/master-build-v2.1.sh
./scripts/master-build-v2.1.sh

# التحقق
chmod +x scripts/verify-all-systems.sh
./scripts/verify-all-systems.sh
```

### التشغيل:
```bash
# تشغيل جميع الخدمات
docker-compose up -d

# أو تشغيل فردي
npm run start:astral
npm run start:ndvi
npm run start:irrigation
npm run start:orchestrator
```

---

## 📡 API Endpoints

### Intelligence API
```http
POST /api/v2/intelligence/generate
Content-Type: application/json

{
  "fieldId": "field-001",
  "date": "2025-12-04",
  "userId": "user-123"
}
```

### Astral API
```http
GET /api/v2/astral/today
GET /api/v2/astral/week?fieldId=field-001
```

### NDVI API
```http
GET /api/v2/ndvi/series?fieldId=field-001&start=2025-01-01&end=2025-12-01
```

### Irrigation API
```http
POST /api/v2/irrigation/recommend
Content-Type: application/json

{
  "fieldId": "field-001"
}
```

---

## 📁 الملفات الرئيسية

| الملف | الوصف |
|-------|-------|
| `services/astral-engine-v2/src/engine/astral-engine.ts` | محرك الفلك الزراعي |
| `services/ndvi-engine-v2/src/ndvi-engine.ts` | محرك NDVI |
| `services/irrigation-controller-v2/src/irrigation-controller.ts` | نظام الري |
| `services/task-optimizer-v2/src/ml/task-optimizer-model.ts` | محسن المهام |
| `services/intelligence-orchestrator/src/orchestrator.ts` | طبقة التكامل |
| `services/dashboard-pro-v3/src/pages/MainDashboard.tsx` | لوحة التحكم |

---

## 🔧 التطوير

### تشغيل الاختبارات:
```bash
npm test
./scripts/test-intelligence-layer.sh
```

### التحقق من الكود:
```bash
npm run lint
npm run typecheck
```

---

## 📜 الترخيص

MIT License - حقوق النشر محفوظة 2025

---

## 👥 المساهمون

- فريق Sahool للتطوير
- مختبر الزراعة الذكية - اليمن

---

## 📞 الدعم

- GitHub Issues: https://github.com/kafaat/sahool-project/issues
- البريد الإلكتروني: support@sahool.dev

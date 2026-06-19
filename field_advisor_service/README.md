# 🧠 Field Advisor Service

**Smart Agricultural Advisory System**

Field Advisor هو خدمة مصغرة (Microservice) ذكية لتقديم توصيات زراعية مبنية على تحليل NDVI، الطقس، التربة، ومرحلة النمو.

---

## 🏗️ Architecture

```
┌──────────────────────────┐
│   Web / Mobile Clients   │
│ - Field Dashboard        │
│ - NDVI Map               │
│ - Advisor Panel          │
└───────────────┬──────────┘
                │ REST API
                ▼
┌────────────────────────────────┐
│    Field Advisor API Service   │  Port: 8001
│  - /advisor/analyze-field      │
│  - /advisor/recommendations    │
│  - /advisor/playbook           │
└───────────────┬────────────────┘
                │
                ▼
     ┌──────────────────────┐
     │  Context Aggregator  │
     │ يجمع سياق الحقل من:  │
     │ - NDVI Service       │
     │ - Weather API        │
     │ - Crop Database      │
     │ - Soil Database      │
     └─────────┬────────────┘
               │
               ▼
   ┌──────────────────────────┐
   │  Advisor Engine Core     │
   │ ┌──────────────────────┐ │
   │ │ Rules Engine         │ │  قواعد ثابتة
   │ └──────────────────────┘ │
   │ ┌──────────────────────┐ │
   │ │ ML Scoring (Future)  │ │  نماذج تعلم آلي
   │ └──────────────────────┘ │
   └─────────┬────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │   Recommendation Store       │
  │  - advisor_sessions          │
  │  - recommendations           │
  │  - alerts                    │
  │  - action_logs               │
  └──────────────────────────────┘
```

---

## 📁 Project Structure

```
field_advisor_service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   └── routes/
│   │       ├── advisor.py      # Advisor endpoints
│   │       └── health.py       # Health checks
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── logging.py          # Logging setup
│   ├── engines/
│   │   └── rules_engine.py     # Rules-based engine
│   ├── models/
│   │   ├── base.py             # Database base
│   │   └── advisor.py          # SQLAlchemy models
│   ├── schemas/
│   │   └── advisor.py          # Pydantic schemas
│   └── services/
│       ├── advisor_service.py  # Main service
│       └── context_aggregator.py # Context collection
├── tests/
│   ├── test_api.py             # API tests
│   └── test_rules_engine.py    # Rules engine tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Using Docker Compose

```bash
cd field_advisor_service
docker-compose up -d
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env

# Run the service
uvicorn app.main:app --reload --port 8001
```

### Access API Documentation

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 📡 API Endpoints

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/analyze-field` | POST | Analyze field and generate recommendations |

### Recommendations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/recommendations/{field_id}` | GET | Get recommendations for field |
| `/advisor/recommendations/{id}/accept` | POST | Accept recommendation |
| `/advisor/recommendations/{id}/dismiss` | POST | Dismiss recommendation |

### Alerts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/alerts/{field_id}` | GET | Get alerts for field |
| `/advisor/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/advisor/alerts/{id}/resolve` | POST | Resolve alert |

### Playbook

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/playbook` | POST | Generate action playbook |

### Actions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/actions/{field_id}` | GET | Get action logs |
| `/advisor/actions/{field_id}` | POST | Create action log |
| `/advisor/actions/{id}/status` | PATCH | Update action status |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advisor/stats/{field_id}` | GET | Get field statistics |

---

## 📊 Request/Response Examples

### Analyze Field

**Request:**
```json
POST /advisor/analyze-field
{
  "field_id": "550e8400-e29b-41d4-a716-446655440000",
  "include_weather": true,
  "include_forecast": true,
  "language": "ar"
}
```

**Response:**
```json
{
  "session_id": "a1b2c3d4-...",
  "field_id": "550e8400-...",
  "analysis_date": "2025-12-02T10:30:00Z",
  "health_score": 72.5,
  "risk_level": "medium",
  "ndvi_trend": "stable",
  "summary": "Field health score: 73/100 (medium risk)...",
  "summary_ar": "درجة صحة الحقل: 73/100 (خطر متوسط)...",
  "recommendations": [
    {
      "id": "rec-123",
      "type": "irrigation",
      "title": "Increase Irrigation for Heat Stress",
      "title_ar": "زيادة الري لمواجهة الإجهاد الحراري",
      "priority": 8,
      "urgency": "urgent",
      "confidence_score": 0.9
    }
  ],
  "alerts": [
    {
      "id": "alert-456",
      "severity": "warning",
      "title": "High Temperature Alert",
      "title_ar": "تنبيه درجة حرارة مرتفعة",
      "alert_type": "temperature_high"
    }
  ],
  "recommendation_count": 5,
  "alert_count": 2,
  "critical_alerts": 0
}
```

### Generate Playbook

**Request:**
```json
POST /advisor/playbook
{
  "field_id": "550e8400-...",
  "time_horizon_days": 14,
  "include_resources": true
}
```

**Response:**
```json
{
  "field_id": "550e8400-...",
  "generated_at": "2025-12-02T10:35:00Z",
  "time_horizon_days": 14,
  "actions": [
    {
      "order": 1,
      "recommendation_id": "rec-123",
      "action_type": "irrigation",
      "title": "Increase Irrigation",
      "scheduled_date": "2025-12-03T06:00:00Z",
      "duration_hours": 2.0,
      "resources": {"water_amount": "20mm"}
    }
  ],
  "total_estimated_hours": 12.5,
  "calendar_view": [...]
}
```

---

## 🧠 Rules Engine

### NDVI Rules

| Condition | Action |
|-----------|--------|
| NDVI < 0.3 | Critical alert + Urgent inspection |
| NDVI < 0.4 | Warning alert |
| NDVI declining | Trend warning |
| Low zones > 20% | Zone intervention recommendation |

### Weather Rules

| Condition | Action |
|-----------|--------|
| Temp > 40°C | Heat stress alert + Irrigation increase |
| Humidity < 30% | Water stress warning |
| Wind > 50 km/h | Spray operations warning |
| Rain forecast | Irrigation adjustment |

### Soil Rules

| Condition | Action |
|-----------|--------|
| Moisture < 25% | Urgent irrigation |
| Nitrogen < 30 ppm | Fertilization recommendation |
| pH < 5.5 | Lime application |
| pH > 8.0 | Sulfur application |

### Growth Stage Rules

| Stage | Action |
|-------|--------|
| Vegetative | Nitrogen focus |
| Flowering | P+K focus |
| < 14 days to harvest | Harvest preparation |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_rules_engine.py -v
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | Database connection |
| `NDVI_SERVICE_URL` | http://localhost:8000 | NDVI service URL |
| `WEATHER_API_URL` | https://api.open-meteo.com/v1 | Weather API |
| `REDIS_URL` | redis://localhost:6379/0 | Redis cache |
| `NDVI_CRITICAL_THRESHOLD` | 0.3 | Critical NDVI level |
| `NDVI_WARNING_THRESHOLD` | 0.4 | Warning NDVI level |
| `RATE_LIMIT_REQUESTS` | 100 | Rate limit per minute |

---

## 📈 Database Schema

```sql
-- Advisor Sessions
CREATE TABLE advisor_sessions (
    id UUID PRIMARY KEY,
    field_id UUID NOT NULL,
    tenant_id UUID,
    analysis_date TIMESTAMP,
    health_score FLOAT,
    risk_level VARCHAR(50),
    ndvi_mean FLOAT,
    ndvi_trend VARCHAR(50)
);

-- Recommendations
CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES advisor_sessions(id),
    field_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    priority INTEGER,
    urgency VARCHAR(50),
    confidence_score FLOAT
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES advisor_sessions(id),
    field_id UUID NOT NULL,
    severity VARCHAR(50),
    status VARCHAR(50),
    alert_type VARCHAR(100),
    threshold_value FLOAT,
    actual_value FLOAT
);

-- Action Logs
CREATE TABLE action_logs (
    id UUID PRIMARY KEY,
    recommendation_id UUID REFERENCES recommendations(id),
    field_id UUID NOT NULL,
    status VARCHAR(50),
    action_type VARCHAR(100),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    outcome VARCHAR(100)
);
```

---

## 🔮 Future Enhancements

- [ ] ML-based anomaly detection
- [ ] Crop disease prediction model
- [ ] Yield estimation
- [ ] Multi-field comparison
- [ ] Integration with IoT sensors
- [ ] Push notifications
- [ ] Historical analytics dashboard

---

## 📝 License

MIT License - Sahool Agriculture Platform

---

**Field Advisor Service v1.0.0**

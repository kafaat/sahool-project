# 🤖 Sahool ML Engine - Advanced Agricultural Intelligence

## Overview

The Sahool ML Engine is a comprehensive machine learning service providing advanced agricultural intelligence through multiple specialized AI models. It powers predictive analytics, disease detection, soil analysis, and weather forecasting for precision agriculture.

## 🎯 Key Features

### 1. **Crop Yield Prediction** 🌾
- Predicts expected crop yields based on multiple factors
- Uses Random Forest Regressor with 15+ features
- Confidence scoring and factor analysis
- Actionable recommendations

**Inputs:**
- NDVI values (vegetation health)
- Weather conditions (temperature, rainfall)
- Soil properties (moisture, pH, EC, NPK)
- Crop type and growth stage
- Field characteristics

**Outputs:**
- Predicted yield (tons/hectare)
- Confidence score
- Contributing factors analysis
- Improvement recommendations

### 2. **Disease Detection** 🔬
- Computer Vision-based crop disease detection
- Detects 10+ common crop diseases
- Real-time image analysis
- Treatment and prevention recommendations

**Supported Diseases:**
- Bacterial spot
- Early blight / Late blight
- Leaf mold
- Septoria leaf spot
- Spider mites
- Target spot
- Mosaic virus
- Yellow leaf curl virus

**Features:**
- CNN-based image classification (TensorFlow/Keras)
- Confidence scoring
- Alternative diagnosis suggestions
- Severity assessment
- Treatment protocols

### 3. **Soil Analysis** 🌱
- Comprehensive soil quality assessment
- Multi-parameter analysis
- Crop suitability recommendations
- Nutrient management advice

**Parameters:**
- pH level
- Electrical Conductivity (EC)
- Macronutrients (N, P, K)
- Moisture content
- Organic matter percentage

**Outputs:**
- Overall quality score
- Component-level scores
- Detailed recommendations
- Crop suitability matrix

### 4. **Weather Forecasting** 🌤️
- ML-based weather prediction
- Time series forecasting
- Agricultural impact assessment
- 7-14 day forecasts

**Parameters:**
- Temperature trends
- Rainfall predictions
- Humidity levels
- Wind speed

**Features:**
- Prophet/LSTM time series models
- Risk assessment (heat stress, frost, drought)
- Irrigation recommendations
- Optimal activity suggestions

---

## 🚀 Quick Start

### Prerequisites

```bash
- Python 3.11+
- TensorFlow 2.14+ or PyTorch 2.1+
- Docker (optional)
```

### Installation

```bash
cd multi-repo/ml-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Running the Service

```bash
# Development mode
uvicorn app.main:app --reload --port 8010

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8010 --workers 4

# With Docker
docker build -t sahool-ml-engine .
docker run -p 8010:8010 sahool-ml-engine
```

### Access API Documentation

- **Swagger UI:** http://localhost:8010/docs
- **ReDoc:** http://localhost:8010/redoc

---

## 📊 API Endpoints

### Crop Yield Prediction

```http
POST /api/v1/predict/crop-yield
Content-Type: application/json

{
  "crop_type": "tomato",
  "field_area": 2.5,
  "ndvi_avg": 0.65,
  "ndvi_min": 0.45,
  "ndvi_max": 0.82,
  "temp_avg": 25.5,
  "temp_min": 18.0,
  "temp_max": 32.0,
  "rainfall_total": 450.0,
  "rainfall_days": 12,
  "soil_moisture_avg": 42.0,
  "soil_ph": 6.5,
  "soil_ec": 0.6,
  "days_since_planting": 75
}
```

**Response:**
```json
{
  "predicted_yield": 8.5,
  "unit": "tons/hectare",
  "confidence": 0.85,
  "total_predicted_yield": 21.25,
  "recommendations": [
    "Conditions are optimal. Continue current management practices."
  ],
  "factors": {
    "ndvi": {"status": "excellent", "impact": "positive"},
    "temperature": {"status": "optimal", "impact": "positive"}
  }
}
```

### Disease Detection

```http
POST /api/v1/detect/disease
Content-Type: multipart/form-data

image: [leaf_image.jpg]
field_id: 123
```

**Response:**
```json
{
  "detected_class": "early_blight",
  "confidence": 0.87,
  "severity": "medium",
  "is_healthy": false,
  "treatment": "Apply fungicides (chlorothalonil, mancozeb)",
  "preventive_measures": "Crop rotation, remove infected debris",
  "urgency": "within_week",
  "recommendations": [
    "Likely Early Blight detected.",
    "Take action within this week to prevent spread."
  ]
}
```

### Soil Analysis

```http
POST /api/v1/analyze/soil
Content-Type: application/json

{
  "ph": 6.2,
  "ec": 0.55,
  "nitrogen": 45,
  "phosphorus": 28,
  "potassium": 135,
  "moisture": 38,
  "organic_matter": 2.8
}
```

**Response:**
```json
{
  "overall_quality": "good",
  "overall_score": 82.5,
  "component_scores": {
    "ph": 100.0,
    "ec": 100.0,
    "nutrients": 87.5,
    "moisture": 80.0,
    "organic_matter": 70.0
  },
  "recommendations": [
    "Soil conditions are optimal. Maintain current practices."
  ],
  "crop_suitability": {
    "wheat": "highly_suitable",
    "tomato": "highly_suitable",
    "potato": "suitable"
  }
}
```

### Weather Forecast

```http
POST /api/v1/forecast/weather
Content-Type: application/json

{
  "forecast_days": 7,
  "historical_data": [...]
}
```

**Response:**
```json
{
  "forecast_period_days": 7,
  "forecasts": [
    {
      "date": "2024-12-02",
      "temperature_high": 28.5,
      "temperature_low": 19.2,
      "rainfall_mm": 5.3,
      "conditions": "light_rain"
    }
  ],
  "summary": {
    "avg_temperature": 24.8,
    "total_rainfall": 32.5,
    "rainy_days": 3
  },
  "agricultural_impact": {
    "risk_level": "low",
    "irrigation_need": "medium",
    "recommendations": [
      "Weather conditions are favorable for normal agricultural operations."
    ]
  }
}
```

### Comprehensive Field Analysis

```http
POST /api/v1/analyze/field-comprehensive
```

Combines all ML models for holistic field analysis.

---

## 🧠 Machine Learning Models

### Model Architecture

| Model | Type | Framework | Input | Output |
|-------|------|-----------|-------|--------|
| Crop Predictor | Random Forest | scikit-learn | 15 features | Yield (tons/ha) |
| Disease Detector | CNN | TensorFlow/Keras | 224x224 RGB | 10 classes |
| Soil Analyzer | Rule-based + ML | Hybrid | 7 parameters | Quality score |
| Weather Forecaster | Time Series | Prophet/LSTM | Historical data | 7-14 day forecast |

### Training Pipeline

```bash
# Train crop yield model
python scripts/train_crop_model.py --data data/crop_yield_data.csv

# Train disease detection model
python scripts/train_disease_model.py --images data/disease_images/

# Fine-tune weather forecaster
python scripts/train_weather_model.py --historical data/weather_history.csv
```

### Model Performance

| Model | Metric | Score |
|-------|--------|-------|
| Crop Predictor | R² Score | 0.82 |
| Disease Detector | Accuracy | 91.5% |
| Disease Detector | F1-Score | 0.89 |
| Weather Forecaster | MAE | 2.3°C |

---

## 🔧 Configuration

### Environment Variables

```bash
# ML Engine
ML_ENGINE_PORT=8010
ML_ENGINE_WORKERS=4

# Model Paths
CROP_MODEL_PATH=models_data/crop_yield_model.pkl
DISEASE_MODEL_PATH=models_data/disease_detector_model.h5

# TensorFlow Settings
TF_CPP_MIN_LOG_LEVEL=2
CUDA_VISIBLE_DEVICES=0  # GPU device

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9091
```

### Model Configuration

Models are loaded from `models_data/` directory:
```
models_data/
├── crop_yield_model.pkl
├── crop_yield_scaler.pkl
├── disease_detector_model.h5
├── weather_forecaster_prophet.pkl
└── soil_analyzer_rules.json
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ app/
COPY models_data/ models_data/

# Expose port
EXPOSE 8010

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

### Docker Compose

```yaml
ml-engine:
  build: ./multi-repo/ml-engine
  container_name: sahool-ml-engine
  ports:
    - "8010:8010"
  environment:
    - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:9000
  volumes:
    - ./models_data:/app/models_data
  restart: unless-stopped
```

---

## 📚 Advanced Usage

### Batch Processing

```python
import requests

# Batch crop prediction
fields_data = [
    {"crop_type": "wheat", "field_area": 5.0, ...},
    {"crop_type": "corn", "field_area": 3.5, ...},
]

response = requests.post(
    "http://localhost:8010/api/v1/predict/crop-yield/batch",
    json=fields_data
)
```

### Custom Model Integration

```python
# app/services/custom_model.py
class CustomPredictor:
    async def load_model(self):
        # Load your custom model
        pass

    async def predict(self, data):
        # Your prediction logic
        pass
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific model tests
pytest tests/test_crop_predictor.py -v

# With coverage
pytest --cov=app --cov-report=html
```

---

## 📈 Performance Optimization

### GPU Acceleration

```python
# Enable GPU for TensorFlow
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    tf.config.experimental.set_memory_growth(gpus[0], True)
```

### Model Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_prediction(features_hash):
    return model.predict(features)
```

### Batch Inference

Process multiple requests together for better GPU utilization.

---

## 🔍 Monitoring & Observability

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

prediction_counter = Counter('ml_predictions_total', 'Total predictions')
prediction_duration = Histogram('ml_prediction_duration_seconds', 'Prediction duration')
```

### Logging

Structured JSON logging for easy parsing:
```json
{
  "timestamp": "2024-12-01T10:00:00Z",
  "level": "INFO",
  "service": "ml-engine",
  "model": "crop_predictor",
  "action": "prediction",
  "duration_ms": 145
}
```

---

## 🤝 Contributing

1. Add new models in `app/services/`
2. Update API routes in `app/api.py`
3. Add tests in `tests/`
4. Update documentation

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- TensorFlow Team
- scikit-learn Contributors
- Facebook Prophet
- OpenCV Community

---

**Built with ❤️ for sustainable and intelligent agriculture**

For support: ml-engine@sahool.com

# 🌾 Field Suite NDVI Project
### Advanced Geospatial NDVI Processing + Field Zoning + Web Visualization
**Part of Sahool Project**

---

## 🚀 Overview

Field Suite NDVI هو نظام متكامل لمعالجة بيانات Sentinel-2، حساب NDVI، استخراج حدود الحقول (Field Boundary Detection)، إنشاء مناطق زراعية (NDVI Zones)، وعرضها مباشرة على الخريطة من خلال واجهة Web مبنية بـ React + MapLibre.

تم تصميم النظام ليكون:

- 🛰 معتمدًا على بيانات Sentinel-2
- 🌱 قادرًا على تحليل صحة النبات
- 🗺 قادرًا على عرض النتائج على خرائط Web
- 🧱 جاهزًا للعمل على Docker (Backend + Web + DB + Nginx)
- 🔌 قابلًا للتوسعة (Field Advisor، Timeline، Anomaly Detection)

---

## 📁 Project Structure

```
field_suite_ndvi_project/
│
├── backend/                    # FastAPI + NDVI Engine
│   ├── main.py                 # API Endpoints
│   ├── db.py                   # Database connection
│   ├── models.py               # SQLAlchemy Models
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/                  # Unit Tests (43 tests)
│   │   ├── test_api.py
│   │   └── test_ndvi_service.py
│   └── services/
│        ├── ndvi_service.py    # NDVI Calculation + Zoning
│        └── sentinel_service.py# Sentinel-2 Downloader
│
├── web/                        # React + MapLibre Web App
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
│
├── docker-compose.yml          # Stack: backend + web + db + nginx
├── nginx.conf                  # Reverse Proxy Configuration
├── setup.sh                    # Automated Setup Script
├── .env.example                # Environment Variables Template
└── README.md
```

---

## 🧠 System Architecture

```
                         ┌──────────────────────────┐
                         │        Web App (React)   │
                         │  - NDVI Upload (B04/B08) │
   User Browser ───────▶ │  - MapLibre Visualization│
                         │  - Zones Overlay         │
                         └───────────────┬──────────┘
                                         │ REST / API
                                         ▼
                         ┌──────────────────────────┐
                         │       Backend (FastAPI)  │
                         │  /fields/ndvi-detect     │
                         │  /fields/{id}/zones      │
                         │  /ndvi/heatmap           │
                         ├───────────────┬──────────┤
                                         │
                              NDVI Engine│
                                         ▼
                         ┌──────────────────────────┐
                         │     NDVI Service         │
                         │ - Compute NDVI           │
                         │ - Polygon Extraction     │
                         │ - NDVI Quantile Zoning   │
                         └───────────────┬──────────┘
                                         │
                           Optional      │ Sentinel Hub API
                                         ▼
                         ┌──────────────────────────┐
                         │   Sentinel Service       │
                         │ - Download Scenes        │
                         │ - Extract B04 / B08      │
                         └──────────────────────────┘
```

---

## 🛠 Installation

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone the Repo

```bash
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project
git checkout claude/field-suite-project-generator-013fvPafsGBgXYCqA4RGreZ3
```

### 2. Setup Environment

```bash
cd field_suite_ndvi_project
cp .env.example .env
# Edit .env with your Sentinel credentials (optional)
```

---

## 🐳 Running with Docker

### Quick Start

```bash
cd field_suite_ndvi_project
./setup.sh
```

### Manual Start

```bash
docker-compose up -d --build
```

### Access Points

| Service | URL |
|---------|-----|
| Web UI | http://localhost:5173 |
| API Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Nginx Proxy | http://localhost:8080 |
| PostgreSQL | localhost:5432 |

---

## 🖼 Features

### 🔹 NDVI Processing
- حساب NDVI من بيانات Sentinel-2 (B04 + B08)
- دعم رفع الملفات من الواجهة
- دعم تحميل البيانات مباشرة عبر Sentinel API
- صيغة NDVI: `(NIR - Red) / (NIR + Red)`

### 🔹 Field Boundary Extraction
- استخراج حدود الحقل تلقائيًا عبر threshold-based contour detection
- Shapely polygon generation
- Largest polygon selection

### 🔹 NDVI Zones
- تقسيم الحقل حسب مستويات NDVI (Quantile-based)
- ألوان متعددة (أحمر/أصفر/أخضر)
- GeoJSON جاهز للعرض
- Configurable zone count (2-5)

### 🔹 Web Visualization
- MapLibre GL map engine
- NDVI Zones Overlay with colors
- Field List with selection
- Interactive threshold slider
- Arabic UI support

### 🔹 Heatmap Generation
- PNG heatmap output
- RdYlGn colormap
- Direct download

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/fields/` | GET | List all fields |
| `/fields/ndvi-detect` | POST | Compute NDVI and create zones |
| `/fields/{id}/zones` | GET | Get field zones as GeoJSON |
| `/ndvi/heatmap` | POST | Generate NDVI heatmap PNG |

### NDVI Detection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | float | 0.4 | NDVI threshold for detection |
| `n_zones` | int | 3 | Number of zones (2-5) |
| `red_band` | file | - | B04 band file (.tif/.jp2) |
| `nir_band` | file | - | B08 band file (.tif/.jp2) |
| `use_sentinel` | bool | false | Use Sentinel API instead |

---

## 🧪 Testing

### Run Tests

```bash
cd field_suite_ndvi_project/backend
python -m pytest tests/ -v
```

### Test Coverage

```
======================== 43 passed ========================
✅ NDVI Computation Tests
✅ Zone Detection Tests
✅ API Endpoint Tests
✅ GeoJSON Output Tests
✅ Threshold Filtering Tests
```

### Manual API Test (curl)

```bash
curl -X POST "http://localhost:8000/fields/ndvi-detect?threshold=0.4&n_zones=3" \
  -F "red_band=@B04.jp2" \
  -F "nir_band=@B08.jp2"
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Sentinel API Credentials
SENTINEL_USER=your_copernicus_username
SENTINEL_PASS=your_copernicus_password

# PostgreSQL Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme_in_production
POSTGRES_DB=fields

# Logging
LOG_LEVEL=INFO

# Web Frontend
VITE_API_BASE=http://localhost:8000
```

---

## 🏭 Production Deployment

### Option A — Docker Compose (Simple)

```bash
docker-compose -f docker-compose.yml up -d
```

### Option B — With Nginx Reverse Proxy

Nginx configuration routes:
- Static web → `web:5173`
- API → `backend:8000`

### Option C — Kubernetes

Ready for Helm charts deployment. Contact for templates.

### Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Add Sentinel API credentials
- [ ] Configure CORS for production domains
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up monitoring and alerts

---

## 🐛 Troubleshooting

### Backend Not Starting?

```bash
docker-compose logs backend
```

Common issues:
- GDAL missing → Check Dockerfile
- Rasterio mismatch → Rebuild image
- PostgreSQL connection → Check db health

### Map Not Showing Zones?

Verify:
1. `/fields/{id}/zones` returns valid GeoJSON
2. Response structure: `{ "type": "FeatureCollection", "features": [...] }`
3. Coordinates are valid (lng/lat ranges)

### Web Not Connecting to API?

Check:
```bash
# .env or environment
VITE_API_BASE=http://localhost:8000
```

Nginx config should have:
```nginx
location /api/ { proxy_pass http://backend:8000/; }
```

---

## 📊 NDVI Reference

| NDVI Range | Interpretation | Color |
|------------|----------------|-------|
| < 0 | Water/Non-vegetation | Blue |
| 0 - 0.2 | Bare soil/Dead plants | Brown |
| 0.2 - 0.4 | Sparse vegetation | Yellow |
| 0.4 - 0.6 | Moderate vegetation | Light Green |
| 0.6 - 0.8 | Dense vegetation | Green |
| > 0.8 | Very healthy vegetation | Dark Green |

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

### Code Style

- Python: PEP 8, type hints
- TypeScript: ESLint, Prettier
- Tests required for new features

---

## 📜 License

Part of Sahool Project - Agricultural Technology Platform

---

## 🎯 Roadmap

- [ ] Field Advisor AI
- [ ] Timeline NDVI Analysis
- [ ] Anomaly Detection
- [ ] Multi-Field Monitoring
- [ ] Crop Recommendation Engine
- [ ] Mobile App (Flutter)
- [ ] Offline Support

---

## 📞 Support

For issues or questions:
- GitHub Issues: [kafaat/sahool-project](https://github.com/kafaat/sahool-project/issues)

---

**Built with ❤️ for precision agriculture**

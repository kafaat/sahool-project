# Sahool - Smart Agricultural Platform

<div align="center">

![Sahool Logo](https://via.placeholder.com/200x80/4CAF50/FFFFFF?text=Sahool)

**منصة زراعية ذكية متكاملة | Integrated Smart Agricultural Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

</div>

## 🌾 Overview

Sahool is an enterprise-grade agricultural platform that combines satellite imagery, weather forecasting, AI-powered insights, and field management into a unified system. Built with modern microservices architecture, it provides farmers and agricultural organizations with data-driven tools for precision farming.

### Key Features

- 🛰️ **Satellite Imagery Analysis**: Automated Sentinel-2 data ingestion and NDVI calculation
- 🌤️ **Weather Forecasting**: Real-time weather data and forecasts from Open-Meteo
- 🤖 **AI Field Assistant**: Intelligent recommendations powered by AI
- 📊 **Field Analytics**: Health scoring, alerts, and timeline visualization
- 🗺️ **Geographic Management**: PostGIS-powered spatial data handling
- 🔐 **Multi-tenant Architecture**: Secure tenant and user management
- 📱 **Modern Web Dashboard**: Responsive Next.js interface
- 🐳 **Cloud-Native**: Docker and Kubernetes ready

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project

# Copy environment template
cp .env.example .env

# Start all services
make up

# Or manually
docker-compose -f docker-compose.enterprise.yml up -d
```

### Access the Platform

- **Web Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:9000
- **API Documentation**: http://localhost:9000/docs
- **MinIO Console**: http://localhost:9001

## 📁 Project Structure

```
sahool-project/
├── multi-repo/                 # Microservices
│   ├── gateway-edge/          # API Gateway
│   ├── geo-core/              # Geographic data service
│   ├── weather-core/          # Weather data service
│   ├── imagery-core/          # Satellite imagery service
│   ├── soil-core/             # Soil data service
│   ├── analytics-core/        # Analytics engine
│   ├── alerts-core/           # Alert management
│   ├── timeline-core/         # Timeline aggregation
│   ├── agent-ai/              # AI assistant
│   ├── ndvi-processor/        # NDVI calculation
│   ├── satellite-ingestor/    # Sentinel-2 ingestion
│   ├── weather-ingestor/      # Weather data ingestion
│   └── platform-core/         # User/tenant management
├── web/                       # Next.js frontend
├── tests/                     # Integration tests
├── helm/                      # Kubernetes deployment
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## 🏗️ Architecture

Sahool follows a microservices architecture with the following layers:

1. **Frontend Layer**: Next.js web application
2. **Gateway Layer**: API gateway with routing, caching, and rate limiting
3. **Core Services**: Domain-specific microservices (geo, weather, imagery, etc.)
4. **Processing Services**: Data ingestion and processing pipelines
5. **Data Layer**: PostgreSQL + PostGIS, Redis, MinIO

See [ARCHITECTURE_v15.md](ARCHITECTURE_v15.md) for detailed architecture documentation.

## 🛠️ Development

### Local Development

```bash
# Start infrastructure only (DB, Redis, MinIO)
make dev

# Run a specific service
cd multi-repo/geo-core/multi-repo/geo-core
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Running Tests

```bash
# Run all tests
make test

# Run specific service tests
cd multi-repo/geo-core/multi-repo/geo-core
pytest -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide.

## 📚 Documentation

- [Development Guide](DEVELOPMENT.md) - Setup and development workflow
- [Enterprise Deployment](README_ENTERPRISE.md) - Production deployment guide
- [Architecture](ARCHITECTURE_v15.md) - System architecture
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [API Documentation](http://localhost:9000/docs) - Interactive API docs (when running)

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/sahool

# Satellite Data (Copernicus)
CDSE_USER=your_username
CDSE_PASS=your_password

# Object Storage
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Cache
REDIS_URL=redis://redis:6379/0
```

## 🌐 API Endpoints

### Core Services

- **Geo Service**: `http://localhost:9000/api/geo/*`
- **Weather Service**: `http://localhost:9000/api/weather/*`
- **Imagery Service**: `http://localhost:9000/api/imagery/*`
- **Analytics Service**: `http://localhost:9000/api/analytics/*`
- **Agent AI**: `http://localhost:9000/api/agent/*`

### Health Checks

```bash
# Check all services
curl http://localhost:9000/health

# Check specific service
curl http://localhost:9000/api/geo/health
```

## 🚢 Deployment

### Docker Compose (Development/Staging)

```bash
docker-compose -f docker-compose.enterprise.yml up -d
```

### Kubernetes (Production)

```bash
cd helm/sahool-platform
helm install sahool-platform . -n sahool --create-namespace
```

See [README_ENTERPRISE.md](README_ENTERPRISE.md) for production deployment details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) for Sentinel-2 data
- [Open-Meteo](https://open-meteo.com/) for weather data
- [FastAPI](https://fastapi.tiangolo.com/) framework
- [Next.js](https://nextjs.org/) framework

## 📞 Support

- 📖 [Documentation](https://github.com/kafaat/sahool-project/wiki)
- 🐛 [Issue Tracker](https://github.com/kafaat/sahool-project/issues)
- 💬 [Discussions](https://github.com/kafaat/sahool-project/discussions)

---

<div align="center">

**Built with ❤️ for sustainable agriculture**

[Website](https://sahool.example.com) • [Documentation](https://docs.sahool.example.com) • [Blog](https://blog.sahool.example.com)

</div>

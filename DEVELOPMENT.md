# Development Guide

This guide provides detailed instructions for setting up and developing the Sahool agricultural platform.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project

# Copy environment template
cp .env.example .env

# Start infrastructure services
make dev

# Or start all services
make up
```

## Architecture Overview

Sahool is built as a microservices architecture with the following components:

### Core Services

- **geo-core**: Geographic data management (fields, boundaries, coordinates)
- **weather-core**: Weather forecasting and historical data
- **imagery-core**: Satellite imagery storage and metadata
- **soil-core**: Soil sample data and analysis
- **analytics-core**: Field health scoring and analytics
- **alerts-core**: Alert generation and notification
- **timeline-core**: Timeline aggregation service

### Processing Services

- **ndvi-processor**: NDVI calculation from satellite imagery
- **satellite-ingestor**: Sentinel-2 data ingestion from CDSE
- **weather-ingestor**: Weather data ingestion from Open-Meteo

### Platform Services

- **gateway-edge**: API gateway with routing and caching
- **agent-ai**: AI-powered field assistant
- **platform-core**: User and tenant management

### Frontend

- **web/**: Next.js farmer dashboard

## Development Workflow

### 1. Working on a Service

```bash
# Navigate to service directory
cd multi-repo/geo-core/multi-repo/geo-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run service locally
uvicorn app.main:app --reload --port 8001
```

### 2. Database Migrations

```bash
# Install Alembic
pip install alembic

# Initialize migrations (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head
```

### 3. Testing

```bash
# Run all tests
make test

# Run specific service tests
cd multi-repo/geo-core/multi-repo/geo-core
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### 4. Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Or manually
black .
ruff check .
```

## Service Development

### Creating a New Service

1. **Create directory structure**:
```bash
mkdir -p multi-repo/new-service/multi-repo/new-service/app/{api/routes,models,schemas,services,core,db}
```

2. **Create `app/main.py`**:
```python
from fastapi import FastAPI

app = FastAPI(title="new-service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "new-service"}
```

3. **Create `Dockerfile`**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

4. **Add to `docker-compose.enterprise.yml`**

5. **Create tests** in `tests/new-service/`

### Database Models

Use SQLAlchemy with GeoAlchemy2 for spatial data:

```python
from sqlalchemy import Column, Integer, String, DateTime
from geoalchemy2 import Geometry
from app.db.base import Base

class Field(Base):
    __tablename__ = "fields"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    geometry = Column(Geometry('POLYGON', srid=4326))
    created_at = Column(DateTime, server_default=func.now())
```

### API Routes

Follow RESTful conventions:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/fields", tags=["fields"])

@router.get("/")
def list_fields(tenant_id: int, db: Session = Depends(get_db)):
    return db.query(Field).filter(Field.tenant_id == tenant_id).all()

@router.post("/")
def create_field(field: FieldCreate, db: Session = Depends(get_db)):
    db_field = Field(**field.dict())
    db.add(db_field)
    db.commit()
    return db_field
```

## Frontend Development

### Running the Web App

```bash
cd web
npm install
npm run dev
```

Access at http://localhost:3000

### Adding a New Page

1. Create file in `web/app/`:
```typescript
// web/app/fields/page.tsx
export default function FieldsPage() {
  return <div>Fields List</div>
}
```

2. Add API integration in `web/lib/api.ts`

3. Create components in `web/components/`

## Docker Development

### Building Images

```bash
# Build specific service
docker build -t sahool-geo-core:dev \
  ./multi-repo/geo-core/multi-repo/geo-core

# Build all services
docker-compose -f docker-compose.enterprise.yml build
```

### Debugging in Docker

```bash
# View logs
docker logs -f sahool-geo-core

# Execute commands in container
docker exec -it sahool-geo-core bash

# Check health
docker inspect --format='{{.State.Health.Status}}' sahool-geo-core
```

## Environment Variables

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MINIO_ENDPOINT`: MinIO object storage endpoint
- `CDSE_USER`, `CDSE_PASS`: Copernicus credentials
- `SAHOOL_ENV`: Environment (local/dev/staging/prod)

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it sahool-postgres psql -U postgres -d sahool
```

### Service Not Starting

```bash
# Check logs
docker logs sahool-geo-core

# Rebuild image
docker-compose -f docker-compose.enterprise.yml build geo-core
docker-compose -f docker-compose.enterprise.yml up -d geo-core
```

### Port Conflicts

```bash
# Find process using port
lsof -i :9000

# Kill process
kill -9 <PID>
```

## Best Practices

1. **Always use type hints** in Python code
2. **Write tests** for new features
3. **Document API endpoints** with docstrings
4. **Use environment variables** for configuration
5. **Follow the existing code structure**
6. **Keep services independent** - avoid tight coupling
7. **Use async/await** for I/O operations
8. **Implement proper error handling**
9. **Add health check endpoints** to all services
10. **Version your APIs** (e.g., `/api/v1/`)

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Copernicus Data Space](https://dataspace.copernicus.eu/)

## Getting Help

- Check existing issues on GitHub
- Review the README and documentation
- Ask in GitHub Discussions
- Contact the maintainers

#!/bin/bash
# ===================================================================
# SAHOOL v6.8.1 - Python Services Complete Setup
# Fixes: Models, Database, Schemas, Services, Requirements
# ===================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()   { echo -e "${GREEN}[PYTHON-FIX]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
header(){ echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}\n${CYAN}$1${NC}\n${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"; }

# ===================== CONFIGURATION =====================
PROJECT_DIR="${1:-sahool-platform-v6-final}"
cd "$PROJECT_DIR" || error "Project directory not found: $PROJECT_DIR"

# Services to fix
SERVICES=("geo-service" "ndvi-engine-service" "zones-engine" "advisor-engine")

# ===================== GEO-SERVICE SETUP =====================
setup_geo_service() {
    log "Setting up geo-service..."
    mkdir -p geo-service
    cd geo-service

    # ✅ models.py - Complete with Field and Task
    cat > models.py <<'EOF'
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Field(Base):
    __tablename__ = "fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    acreage = Column(Float)
    ndvi_value = Column(Float)
    boundary = Column(Text)  # GeoJSON
    color = Column(String(7), default="#4CAF50")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "acreage": self.acreage,
            "ndvi_value": self.ndvi_value,
            "boundary": self.boundary,
            "color": self.color,
            "created_at": self.created_at.isoformat()
        }

class FieldTask(Base):
    __tablename__ = "field_tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
EOF

    # ✅ database.py
    cat > database.py <<'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

    # ✅ schemas.py
    cat > schemas.py <<'EOF'
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FieldBase(BaseModel):
    tenant_id: str
    name: str
    acreage: Optional[float] = None
    ndvi_value: Optional[float] = None
    boundary: Optional[str] = None
    color: Optional[str] = "#4CAF50"

class FieldCreate(FieldBase):
    pass

class FieldUpdate(BaseModel):
    name: Optional[str] = None
    acreage: Optional[float] = None
    ndvi_value: Optional[float] = None
    color: Optional[str] = None

class Field(FieldBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
EOF

    # ✅ field_service.py
    cat > field_service.py <<'EOF'
from typing import List
from sqlalchemy.orm import Session
import models
import schemas

def list_fields(db: Session, tenant_id: str) -> List[models.Field]:
    return db.query(models.Field).filter(
        models.Field.tenant_id == tenant_id,
        models.Field.acreage > 0
    ).all()

def create_field(db: Session, field: schemas.FieldCreate) -> models.Field:
    db_field = models.Field(**field.dict())
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field

def get_field(db: Session, field_id: str, tenant_id: str) -> models.Field:
    return db.query(models.Field).filter(
        models.Field.id == field_id,
        models.Field.tenant_id == tenant_id
    ).first()
EOF

    # ✅ main.py - Complete FastAPI
    cat > main.py <<'EOF'
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
import database
import field_service

app = FastAPI(title="SAHOOL Geo Service", version="6.8.1")

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/health")
def health():
    return {"status": "ok", "service": "geo-service", "version": "6.8.1"}

@app.get("/fields", response_model=List[dict])
def read_fields(tenant_id: str, db: Session = Depends(database.get_db)):
    fields = field_service.list_fields(db, tenant_id)
    return [f.to_dict() for f in fields]

@app.post("/fields", response_model=dict)
def create_field(field: schemas.FieldCreate, db: Session = Depends(database.get_db)):
    return field_service.create_field(db, field).to_dict()

@app.get("/fields/{field_id}", response_model=dict)
def read_field(field_id: str, tenant_id: str, db: Session = Depends(database.get_db)):
    field = field_service.get_field(db, field_id, tenant_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field.to_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
EOF

    # ✅ requirements.txt
    cat > requirements.txt <<'EOF'
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
pydantic==2.6.1
python-dotenv==1.0.1
python-multipart==0.0.9
EOF

    # ✅ Dockerfile
    cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
EOF

    # ✅ .dockerignore
    cat > .dockerignore <<'EOF'
__pycache__
*.pyc
.pytest_cache
.env
.venv
*.db
EOF

    cd ..
    log "✓ geo-service configured"
}

# ===================== NDVI ENGINE SETUP =====================
setup_ndvi_service() {
    log "Setting up ndvi-engine-service..."
    mkdir -p ndvi-engine-service
    cd ndvi-engine-service

    # ✅ models.py
    cat > models.py <<'EOF'
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class NDVIRecord(Base):
    __tablename__ = "ndvi_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ndvi_value = Column(Float, nullable=False)
    image_url = Column(String(500))
    captured_at = Column(DateTime, default=datetime.utcnow)
EOF

    # ✅ database.py
    cat > database.py <<'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

    # ✅ schemas.py
    cat > schemas.py <<'EOF'
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NDVIRecordBase(BaseModel):
    field_id: str
    ndvi_value: float
    image_url: Optional[str] = None

class NDVIRecordCreate(NDVIRecordBase):
    pass

class NDVIRecord(NDVIRecordBase):
    id: str
    captured_at: datetime

    class Config:
        orm_mode = True
EOF

    # ✅ worker.py
    cat > worker.py <<'EOF'
import os
import sys
import redis
from rq import Connection, Worker
from sqlalchemy import create_engine

REDIS_URL = os.getenv("REDIS_URL", "redis://:password@redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")
engine = create_engine(DATABASE_URL)

def process_ndvi(field_id: str):
    """Simulate NDVI processing"""
    print(f"[WORKER] Processing NDVI for field: {field_id}")
    return {"field_id": field_id, "ndvi": 0.72}

if __name__ == "__main__":
    try:
        conn = redis.from_url(REDIS_URL)
        with Connection(conn):
            worker = Worker(['ndvi-queue'])
            print("[WORKER] Starting NDVI worker...")
            worker.work()
    except Exception as e:
        print(f"[FATAL] Worker failed: {e}", file=sys.stderr)
        sys.exit(1)
EOF

    # ✅ main.py
    cat > main.py <<'EOF'
from fastapi import FastAPI, BackgroundTasks
import os
import redis
from rq import Queue
import models
import database

app = FastAPI(title="SAHOOL NDVI Engine", version="6.8.1")

REDIS_URL = os.getenv("REDIS_URL", "redis://:password@redis:6379")
redis_conn = redis.from_url(REDIS_URL)
ndvi_queue = Queue('ndvi-queue', connection=redis_conn)

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/health")
def health():
    try:
        queue_size = len(ndvi_queue)
    except:
        queue_size = -1
    return {"status": "ok", "service": "ndvi-engine", "queue_size": queue_size}

@app.post("/process/{field_id}")
def process_ndvi(field_id: str):
    job = ndvi_queue.enqueue('worker.process_ndvi', field_id)
    return {"job_id": job.id, "status": "queued"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
EOF

    # ✅ requirements.txt
    cat > requirements.txt <<'EOF'
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
pydantic==2.6.1
python-dotenv==1.0.1
redis==5.0.1
rq==1.15.1
EOF

    # ✅ Dockerfile
    cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
EOF

    # ✅ .dockerignore
    cat > .dockerignore <<'EOF'
__pycache__
*.pyc
.pytest_cache
.env
.venv
EOF

    cd ..
    log "✓ ndvi-engine-service configured"
}

# ===================== ZONES ENGINE SETUP =====================
setup_zones_service() {
    log "Setting up zones-engine..."
    mkdir -p zones-engine
    cd zones-engine

    # ✅ models.py
    cat > models.py <<'EOF'
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Zone(Base):
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    zone_type = Column(String(50), nullable=False)
    geometry = Column(JSON)
    productivity_index = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
EOF

    # ✅ database.py
    cat > database.py <<'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

    # ✅ schemas.py
    cat > schemas.py <<'EOF'
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ZoneBase(BaseModel):
    field_id: str
    zone_type: str
    geometry: Optional[Dict] = None
    productivity_index: Optional[float] = None

class ZoneCreate(ZoneBase):
    pass

class Zone(ZoneBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
EOF

    # ✅ zone_service.py
    cat > zone_service.py <<'EOF'
from sqlalchemy.orm import Session
from typing import List
import models

def generate_zones(db: Session, field_id: str) -> List[models.Zone]:
    # TODO: Implement zone generation algorithm
    return []
EOF

    # ✅ main.py
    cat > main.py <<'EOF'
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
import models
import database
import zone_service

app = FastAPI(title="SAHOOL Zones Engine", version="6.8.1")

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/health")
def health():
    return {"status": "ok", "service": "zones-engine"}

@app.post("/zones/generate/{field_id}")
def generate_zones(field_id: str, db: Session = Depends(database.get_db)):
    zones = zone_service.generate_zones(db, field_id)
    return {"field_id": field_id, "zones": zones}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
EOF

    # ✅ requirements.txt
    cat > requirements.txt <<'EOF'
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
pydantic==2.6.1
python-dotenv==1.0.1
EOF

    # ✅ Dockerfile
    cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
EOF

    # ✅ .dockerignore
    cat > .dockerignore <<'EOF'
__pycache__
*.pyc
.pytest_cache
.env
.venv
EOF

    cd ..
    log "✓ zones-engine configured"
}

# ===================== ADVISOR ENGINE SETUP =====================
setup_advisor_service() {
    log "Setting up advisor-engine..."
    mkdir -p advisor-engine
    cd advisor-engine

    # ✅ models.py
    cat > models.py <<'EOF'
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recommendation_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    ack_at = Column(DateTime, nullable=True)
EOF

    # ✅ database.py
    cat > database.py <<'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

    # ✅ schemas.py
    cat > schemas.py <<'EOF'
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RecommendationBase(BaseModel):
    field_id: str
    recommendation_type: str
    message: str
    priority: Optional[str] = "medium"

class RecommendationCreate(RecommendationBase):
    pass

class Recommendation(RecommendationBase):
    id: str
    created_at: datetime
    ack_at: Optional[datetime] = None

    class Config:
        orm_mode = True
EOF

    # ✅ advisor_service.py
    cat > advisor_service.py <<'EOF'
from sqlalchemy.orm import Session
from typing import List
import models

def generate_recommendations(db: Session, field_id: str) -> List[dict]:
    # Placeholder recommendation
    return [{
        "field_id": field_id,
        "recommendation_type": "irrigation",
        "message": "زيادة الري بنسبة 20% بسبب ارتفاع الحرارة",
        "priority": "medium"
    }]
EOF

    # ✅ main.py
    cat > main.py <<'EOF'
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
import models
import database
import advisor_service

app = FastAPI(title="SAHOOL Advisor Engine", version="6.8.1")

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/health")
def health():
    return {"status": "ok", "service": "advisor-engine"}

@app.post("/advise/{field_id}")
def get_advice(field_id: str, db: Session = Depends(database.get_db)):
    recommendations = advisor_service.generate_recommendations(db, field_id)
    return {"field_id": field_id, "recommendations": recommendations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
EOF

    # ✅ requirements.txt
    cat > requirements.txt <<'EOF'
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
pydantic==2.6.1
python-dotenv==1.0.1
EOF

    # ✅ Dockerfile
    cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
EOF

    # ✅ .dockerignore
    cat > .dockerignore <<'EOF'
__pycache__
*.pyc
.pytest_cache
.env
.venv
EOF

    cd ..
    log "✓ advisor-engine configured"
}

# ===================== MAIN EXECUTION =====================
main() {
    header "SAHOOL v6.8.1 Python Services Complete Setup"

    for service in "${SERVICES[@]}"; do
        case $service in
            "geo-service") setup_geo_service ;;
            "ndvi-engine-service") setup_ndvi_service ;;
            "zones-engine") setup_zones_service ;;
            "advisor-engine") setup_advisor_service ;;
        esac
    done

    header "Docker Rebuild"
    log "Rebuilding Python services..."
    docker compose build "${SERVICES[@]}" 2>/dev/null || warn "Docker build skipped (run manually)"

    log "Restarting services..."
    docker compose up -d "${SERVICES[@]}" 2>/dev/null || warn "Docker up skipped (run manually)"

    header "✅ Setup Complete!"
    log "All Python services are now properly configured with:"
    log "  - SQLAlchemy models"
    log "  - Pydantic schemas"
    log "  - Database connection pooling"
    log "  - FastAPI endpoints"
    log "  - Health check endpoints"
    echo ""
    log "Next: Run E2E tests to verify: ./e2e_test_sahool_v6_8_1.sh"
}

main "$@"

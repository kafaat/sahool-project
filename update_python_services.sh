#!/bin/bash
# ===================================================================
# SAHOOL v6.8.1 - Python Services Updater
# Fixes: Missing models, schemas, database files for EXISTING services
# Use AFTER cloning from GitHub
# ===================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()   { echo -e "${GREEN}[UPDATER]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
header(){ echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}\n${CYAN}$1${NC}\n${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"; }

# ===================== CONFIGURATION =====================
PROJECT_DIR="${1:-sahool-platform-v6-final}"
cd "$PROJECT_DIR" || error "Project directory not found: $PROJECT_DIR"

# Verify we're in the right place
if [[ ! -f "docker-compose.yml" ]]; then
    error "docker-compose.yml not found. Run from project root."
fi

SERVICES=("geo-service" "ndvi-engine-service" "zones-engine" "advisor-engine")

# ===================== DETECT & FIX =====================
for SERVICE in "${SERVICES[@]}"; do
    if [[ ! -d "$SERVICE" ]]; then
        warn "Service not found: $SERVICE"
        continue
    fi

    log "Updating $SERVICE..."
    cd "$SERVICE"

    # 1. Add __init__.py (required for Python imports)
    if [[ ! -f "__init__.py" ]]; then
        log "  Adding __init__.py..."
        echo "# SAHOOL $SERVICE v6.8.1" > __init__.py
        echo "from . import models, database, schemas" >> __init__.py
    fi

    # 2. Add models.py (critical - fixes AttributeError)
    if [[ ! -f "models.py" ]]; then
        log "  Adding models.py..."
        cat > models.py <<'EOF'
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
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
    boundary = Column(Text)  # GeoJSON string
    color = Column(String(7), default="#4CAF50")
    is_active = Column(Boolean, default=True)
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
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }

class FieldTask(Base):
    __tablename__ = "field_tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

def get_base():
    return Base
EOF
    fi

    # 3. Add database.py (connection pooling)
    if [[ ! -f "database.py" ]]; then
        log "  Adding database.py..."
        cat > database.py <<'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sahool_admin:password@db:5432/sahool_prod")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
    fi

    # 4. Add schemas.py (Pydantic validation)
    if [[ ! -f "schemas.py" ]]; then
        log "  Adding schemas.py..."
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
    fi

    # 5. Add service layer (geo-service only)
    if [[ "$SERVICE" == "geo-service" ]] && [[ ! -f "field_service.py" ]]; then
        log "  Adding field_service.py..."
        cat > field_service.py <<'EOF'
from typing import List
from sqlalchemy.orm import Session
from . import models

def list_fields(db: Session, tenant_id: str) -> List[models.Field]:
    return db.query(models.Field).filter(
        models.Field.tenant_id == tenant_id,
        models.Field.is_active == True
    ).all()

def get_field(db: Session, field_id: str, tenant_id: str) -> models.Field:
    return db.query(models.Field).filter(
        models.Field.id == field_id,
        models.Field.tenant_id == tenant_id
    ).first()
EOF
    fi

    # 6. Add worker.py (ndvi-engine-service only)
    if [[ "$SERVICE" == "ndvi-engine-service" ]] && [[ ! -f "worker.py" ]]; then
        log "  Adding worker.py..."
        cat > worker.py <<'EOF'
import os
import sys
from redis import Redis
from rq import Connection, Worker

REDIS_URL = os.getenv("REDIS_URL", "redis://:password@redis:6379")

def process_ndvi(field_id: str):
    print(f"[WORKER] Processing NDVI for field: {field_id}")
    # TODO: Add actual NDVI calculation logic
    return {"field_id": field_id, "ndvi": 0.72, "status": "completed"}

if __name__ == "__main__":
    try:
        with Connection(Redis.from_url(REDIS_URL)):
            worker = Worker(['ndvi-queue'], connection=Redis.from_url(REDIS_URL))
            print("[WORKER] Starting NDVI worker...")
            worker.work()
    except Exception as e:
        print(f"[FATAL] Worker failed: {e}", file=sys.stderr)
        sys.exit(1)
EOF
    fi

    # 7. Fix main.py (backup + update)
    if [[ -f "main.py" ]]; then
        log "  Checking main.py..."
        if ! grep -q "from . import models" main.py; then
            log "    Updating imports in main.py..."
            cp main.py main.py.backup
            cat > main.py <<'EOF'
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from . import models, database, schemas

# Import service layer if exists
try:
    from . import field_service
except ImportError:
    field_service = None

app = FastAPI(
    title="SAHOOL Service",
    version="6.8.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
def startup_event():
    """Create tables on startup"""
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "version": "6.8.1"
    }

@app.get("/fields", response_model=List[dict])
def read_fields(tenant_id: str, db: Session = Depends(database.get_db)):
    """List all fields for a tenant"""
    fields = db.query(models.Field).filter(models.Field.tenant_id == tenant_id).all()
    return [f.to_dict() for f in fields if hasattr(f, 'to_dict')] if fields else []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
EOF
        fi
    fi

    # 8. Fix requirements.txt
    if [[ ! -f "requirements.txt" ]]; then
        log "  Adding requirements.txt..."
        cat > requirements.txt <<'EOF'
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
pydantic==2.6.1
python-dotenv==1.0.1
python-multipart==0.0.9
EOF
    fi

    # 9. Add .dockerignore
    if [[ ! -f ".dockerignore" ]]; then
        log "  Adding .dockerignore..."
        cat > .dockerignore <<'EOF'
__pycache__
*.pyc
.pytest_cache
.env
.venv
*.db
.git
EOF
    fi

    cd ..
    log "✓ $SERVICE updated successfully"
done

# ===================== DOCKER REBUILD =====================
header "Docker Rebuild"
log "Stopping Python services..."
docker compose stop "${SERVICES[@]}" 2>/dev/null || true

log "Building updated services..."
docker compose build "${SERVICES[@]}"

log "Starting services..."
docker compose up -d "${SERVICES[@]}"

# ===================== VERIFICATION =====================
header "Verification"
log "Waiting 15 seconds for services to start..."
sleep 15

for SERVICE in "${SERVICES[@]}"; do
    STATUS=$(docker compose ps "$SERVICE" --format json 2>/dev/null | jq -r '.State' 2>/dev/null || echo "unknown")
    if [[ "$STATUS" == "running" ]]; then
        log "✓ $SERVICE is running"
    else
        warn "! $SERVICE status: $STATUS"
    fi
done

# Test health endpoints if curl available
if command -v curl &>/dev/null; then
    log "Testing health endpoints..."
    for SERVICE in "${SERVICES[@]}"; do
        PORT=$(docker compose port "$SERVICE" 3000 2>/dev/null | cut -d: -f2)
        if [[ -n "$PORT" ]]; then
            if curl -s -f "http://localhost:$PORT/health" >/dev/null 2>&1; then
                log "✓ $SERVICE health check passed (port $PORT)"
            else
                warn "! $SERVICE health check failed"
            fi
        fi
    done
fi

header "✅ Python Services Update Complete!"
log "All missing files have been added and services rebuilt."
log "Next: Run E2E tests to verify: ./e2e_test_sahool_v6_8_1.sh"
log "If tests pass, commit changes to GitHub:"
log "  git add ."
log "  git commit -m 'fix: Add missing Python service files'"
log "  git push origin master"

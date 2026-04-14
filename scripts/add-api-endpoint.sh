#!/bin/bash
set -e

# =====================================
# Field Suite - Add API Endpoint Script
# يضيف endpoint جديد للـ API تلقائياً
# Version: 1.0.0
# =====================================

# الألوان
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# =====================================
# 🛠️ دوال مساعدة
# =====================================
log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

log_info() {
    echo -e "${CYAN}ℹ️${NC} $1"
}

# =====================================
# 📋 التحقق من المعاملات
# =====================================
if [ -z "$1" ]; then
    log_error "استخدام: ./add-api-endpoint.sh <اسم_endpoint> [OPTIONS]"
    echo ""
    echo "الخيارات:"
    echo "  --schema    إنشاء ملف schema"
    echo "  --test      إنشاء ملف اختبار"
    echo "  --full      إنشاء schema + test + CRUD كامل"
    echo ""
    echo "أمثلة:"
    echo "  ./add-api-endpoint.sh analytics"
    echo "  ./add-api-endpoint.sh crop-prediction --full"
    echo "  ./add-api-endpoint.sh irrigation --schema --test"
    exit 1
fi

ENDPOINT_NAME=$1
shift

# قراءة الخيارات
CREATE_SCHEMA=false
CREATE_TEST=false
FULL_CRUD=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --schema) CREATE_SCHEMA=true ;;
        --test) CREATE_TEST=true ;;
        --full)
            CREATE_SCHEMA=true
            CREATE_TEST=true
            FULL_CRUD=true
            ;;
        *) log_warning "خيار غير معروف: $1" ;;
    esac
    shift
done

# =====================================
# 📁 إعداد المسارات
# =====================================
PROJECT_DIR="field_suite_full_project"
BACKEND_DIR="$PROJECT_DIR/backend"

# تحويل الاسم (kebab-case → snake_case)
FILE_NAME=$(echo "$ENDPOINT_NAME" | tr '-' '_')
# تحويل إلى PascalCase
CAMEL_NAME=$(echo "$ENDPOINT_NAME" | sed -r 's/(^|-)([a-z])/\U\2/g')

log_info "إنشاء endpoint: $ENDPOINT_NAME"
log_info "اسم الملف: $FILE_NAME"
log_info "اسم الـ Class: $CAMEL_NAME"
echo ""

# التحقق من وجود المجلدات
mkdir -p "$BACKEND_DIR/app/api/v1"
mkdir -p "$BACKEND_DIR/app/schemas"
mkdir -p "$BACKEND_DIR/app/services"
mkdir -p "$BACKEND_DIR/app/models"
mkdir -p "$BACKEND_DIR/tests/unit"

# =====================================
# 1️⃣ إنشاء Router ملف
# =====================================
log_success "إنشاء router: ${FILE_NAME}.py"

ROUTER_FILE="$BACKEND_DIR/app/api/v1/${FILE_NAME}.py"

cat > "$ROUTER_FILE" << EOF
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, TokenData

router = APIRouter()

# =====================================
# ${CAMEL_NAME} Endpoints
# =====================================

@router.get("/${ENDPOINT_NAME}", response_model=List[dict])
async def get_all_${FILE_NAME}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    جلب كل عناصر ${ENDPOINT_NAME} مع دعم pagination

    - **skip**: عدد العناصر المراد تخطيها
    - **limit**: الحد الأقصى للعناصر المرجعة
    """
    # TODO: Implement get_all logic
    return []

@router.get("/${ENDPOINT_NAME}/{item_id}")
async def get_${FILE_NAME}(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    جلب عنصر ${ENDPOINT_NAME} محدد بواسطة ID
    """
    # TODO: Implement get_by_id logic
    raise HTTPException(status_code=404, detail="${CAMEL_NAME} not found")

@router.post("/${ENDPOINT_NAME}", status_code=201)
async def create_${FILE_NAME}(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    إنشاء عنصر ${ENDPOINT_NAME} جديد
    """
    # TODO: Implement create logic
    return {"message": "${CAMEL_NAME} created successfully"}

@router.put("/${ENDPOINT_NAME}/{item_id}")
async def update_${FILE_NAME}(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تحديث عنصر ${ENDPOINT_NAME} موجود
    """
    # TODO: Implement update logic
    raise HTTPException(status_code=404, detail="${CAMEL_NAME} not found")

@router.delete("/${ENDPOINT_NAME}/{item_id}", status_code=204)
async def delete_${FILE_NAME}(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    حذف عنصر ${ENDPOINT_NAME}
    """
    # TODO: Implement delete logic
    return None

@router.get("/${ENDPOINT_NAME}/stats/summary")
async def get_${FILE_NAME}_stats(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    جلب إحصائيات عامة عن ${ENDPOINT_NAME}
    """
    return {
        "total_count": 0,
        "tenant_id": current_user.tenant_id,
        "message": "Stats endpoint ready"
    }
EOF

# =====================================
# 2️⃣ إنشاء ملف Schema (إذا طُلب)
# =====================================
if [ "$CREATE_SCHEMA" = true ]; then
    log_success "إنشاء schema: ${FILE_NAME}.py"

    SCHEMA_FILE="$BACKEND_DIR/app/schemas/${FILE_NAME}.py"

    cat > "$SCHEMA_FILE" << EOF
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime

# =====================================
# ${CAMEL_NAME} Schemas
# =====================================

class ${CAMEL_NAME}Base(BaseModel):
    """النموذج الأساسي لـ ${ENDPOINT_NAME}"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None

class ${CAMEL_NAME}Create(${CAMEL_NAME}Base):
    """نموذج إنشاء ${ENDPOINT_NAME}"""
    pass

class ${CAMEL_NAME}Update(BaseModel):
    """نموذج تحديث ${ENDPOINT_NAME}"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None

class ${CAMEL_NAME}Response(${CAMEL_NAME}Base):
    """نموذج استجابة ${ENDPOINT_NAME}"""
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ${CAMEL_NAME}Stats(BaseModel):
    """إحصائيات ${ENDPOINT_NAME}"""
    total_count: int
    active_count: int = 0
    average_value: Optional[float] = None
    last_updated: Optional[datetime] = None

class ${CAMEL_NAME}ListResponse(BaseModel):
    """استجابة قائمة ${ENDPOINT_NAME} مع pagination"""
    items: List[${CAMEL_NAME}Response]
    total: int
    skip: int
    limit: int
EOF
fi

# =====================================
# 3️⃣ إنشاء ملف Service (إذا طلب full CRUD)
# =====================================
if [ "$FULL_CRUD" = true ]; then
    log_success "إنشاء service: ${FILE_NAME}_service.py"

    SERVICE_FILE="$BACKEND_DIR/app/services/${FILE_NAME}_service.py"

    cat > "$SERVICE_FILE" << EOF
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.${FILE_NAME} import ${CAMEL_NAME}
from app.schemas.${FILE_NAME} import ${CAMEL_NAME}Create, ${CAMEL_NAME}Update

class ${CAMEL_NAME}Service:
    """
    Service layer for ${CAMEL_NAME} operations
    Handles business logic and database interactions
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[${CAMEL_NAME}]:
        """Get all ${ENDPOINT_NAME}s for a tenant with pagination"""
        return (
            self.db.query(${CAMEL_NAME})
            .filter(${CAMEL_NAME}.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, item_id: int, tenant_id: int) -> Optional[${CAMEL_NAME}]:
        """Get a specific ${ENDPOINT_NAME} by ID"""
        return (
            self.db.query(${CAMEL_NAME})
            .filter(
                ${CAMEL_NAME}.id == item_id,
                ${CAMEL_NAME}.tenant_id == tenant_id
            )
            .first()
        )

    def create(self, item: ${CAMEL_NAME}Create, tenant_id: int) -> ${CAMEL_NAME}:
        """Create a new ${ENDPOINT_NAME}"""
        db_item = ${CAMEL_NAME}(
            **item.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def update(
        self,
        item_id: int,
        item: ${CAMEL_NAME}Update,
        tenant_id: int
    ) -> Optional[${CAMEL_NAME}]:
        """Update an existing ${ENDPOINT_NAME}"""
        db_item = self.get_by_id(item_id, tenant_id)
        if db_item:
            update_data = item.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_item, field, value)
            self.db.commit()
            self.db.refresh(db_item)
        return db_item

    def delete(self, item_id: int, tenant_id: int) -> bool:
        """Delete a ${ENDPOINT_NAME}"""
        db_item = self.get_by_id(item_id, tenant_id)
        if db_item:
            self.db.delete(db_item)
            self.db.commit()
            return True
        return False

    def get_count(self, tenant_id: int) -> int:
        """Get total count of ${ENDPOINT_NAME}s for a tenant"""
        return (
            self.db.query(func.count(${CAMEL_NAME}.id))
            .filter(${CAMEL_NAME}.tenant_id == tenant_id)
            .scalar()
        )

    def get_stats(self, tenant_id: int) -> dict:
        """Get statistics for ${ENDPOINT_NAME}s"""
        total = self.get_count(tenant_id)
        return {
            "total_count": total,
            "active_count": total,  # TODO: Add active status filter
            "tenant_id": tenant_id
        }
EOF
fi

# =====================================
# 4️⃣ إنشاء ملف Model (إذا طلب full CRUD)
# =====================================
if [ "$FULL_CRUD" = true ]; then
    log_success "إنشاء model: ${FILE_NAME}.py"

    MODEL_FILE="$BACKEND_DIR/app/models/${FILE_NAME}.py"

    cat > "$MODEL_FILE" << EOF
from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base

class ${CAMEL_NAME}(Base):
    """
    ${CAMEL_NAME} Model

    Represents a ${ENDPOINT_NAME} entity in the database.
    """
    __tablename__ = "${FILE_NAME}s"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def __repr__(self):
        return f"<${CAMEL_NAME}(id={self.id}, name='{self.name}')>"
EOF
fi

# =====================================
# 5️⃣ إنشاء ملف اختبار (إذا طُلب)
# =====================================
if [ "$CREATE_TEST" = true ]; then
    log_success "إنشاء test: test_${FILE_NAME}.py"

    TEST_FILE="$BACKEND_DIR/tests/unit/test_${FILE_NAME}.py"

    cat > "$TEST_FILE" << EOF
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the app
from app.main import app

client = TestClient(app)

# Mock authentication
@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def mock_current_user():
    with patch("app.core.security.get_current_user") as mock:
        mock.return_value = MagicMock(
            sub="test@example.com",
            tenant_id=1,
            is_admin=False
        )
        yield mock

# =====================================
# ${CAMEL_NAME} API Tests
# =====================================

class Test${CAMEL_NAME}Endpoints:
    """Test suite for ${ENDPOINT_NAME} endpoints"""

    def test_get_all_${FILE_NAME}s(self, auth_headers, mock_current_user):
        """Test GET /api/v1/${ENDPOINT_NAME}"""
        response = client.get(
            "/api/v1/${ENDPOINT_NAME}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_all_${FILE_NAME}s_with_pagination(self, auth_headers, mock_current_user):
        """Test GET /api/v1/${ENDPOINT_NAME} with pagination"""
        response = client.get(
            "/api/v1/${ENDPOINT_NAME}?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_${FILE_NAME}_not_found(self, auth_headers, mock_current_user):
        """Test GET /api/v1/${ENDPOINT_NAME}/{id} - not found"""
        response = client.get(
            "/api/v1/${ENDPOINT_NAME}/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_${FILE_NAME}(self, auth_headers, mock_current_user):
        """Test POST /api/v1/${ENDPOINT_NAME}"""
        data = {
            "name": "Test ${CAMEL_NAME}",
            "description": "Test description"
        }
        response = client.post(
            "/api/v1/${ENDPOINT_NAME}",
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_get_${FILE_NAME}_stats(self, auth_headers, mock_current_user):
        """Test GET /api/v1/${ENDPOINT_NAME}/stats/summary"""
        response = client.get(
            "/api/v1/${ENDPOINT_NAME}/stats/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "total_count" in response.json()

    def test_unauthorized_access(self):
        """Test unauthorized access returns 401/403"""
        response = client.get("/api/v1/${ENDPOINT_NAME}")
        assert response.status_code in [401, 403]
EOF
fi

# =====================================
# 6️⃣ إنشاء Alembic Migration (إذا طلب full CRUD)
# =====================================
if [ "$FULL_CRUD" = true ]; then
    log_success "إنشاء migration template"

    MIGRATION_DIR="$BACKEND_DIR/migrations/versions"
    mkdir -p "$MIGRATION_DIR"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    MIGRATION_FILE="$MIGRATION_DIR/${TIMESTAMP}_add_${FILE_NAME}_table.py"

    cat > "$MIGRATION_FILE" << EOF
"""Add ${FILE_NAME} table

Revision ID: ${TIMESTAMP}
Revises:
Create Date: $(date +%Y-%m-%d\ %H:%M:%S)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '${TIMESTAMP}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        '${FILE_NAME}s',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_${FILE_NAME}s_id', '${FILE_NAME}s', ['id'])
    op.create_index('ix_${FILE_NAME}s_tenant_id', '${FILE_NAME}s', ['tenant_id'])

def downgrade():
    op.drop_index('ix_${FILE_NAME}s_tenant_id', '${FILE_NAME}s')
    op.drop_index('ix_${FILE_NAME}s_id', '${FILE_NAME}s')
    op.drop_table('${FILE_NAME}s')
EOF
fi

# =====================================
# 7️⃣ الخاتمة
# =====================================
echo ""
echo "═══════════════════════════════════════════════════════════"
log_success "تم إنشاء الـ endpoint بنجاح!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "الملفات المُنشأة:"
echo -e "  ${GREEN}📄${NC} Router:  $ROUTER_FILE"
[ "$CREATE_SCHEMA" = true ] && echo -e "  ${GREEN}📄${NC} Schema:  $BACKEND_DIR/app/schemas/${FILE_NAME}.py"
[ "$FULL_CRUD" = true ] && echo -e "  ${GREEN}📄${NC} Service: $BACKEND_DIR/app/services/${FILE_NAME}_service.py"
[ "$FULL_CRUD" = true ] && echo -e "  ${GREEN}📄${NC} Model:   $BACKEND_DIR/app/models/${FILE_NAME}.py"
[ "$CREATE_TEST" = true ] && echo -e "  ${GREEN}🧪${NC} Test:    $TEST_FILE"
[ "$FULL_CRUD" = true ] && echo -e "  ${GREEN}📄${NC} Migration: $MIGRATION_FILE"
echo ""
echo -e "${CYAN}الرابط الجديد:${NC} http://localhost:8000/api/v1/$ENDPOINT_NAME"
echo ""
echo "═══════════════════════════════════════════════════════════"
log_warning "الخطوات التالية:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. أضف الـ router في main.py:"
echo -e "   ${CYAN}from app.api.v1 import ${FILE_NAME}${NC}"
echo -e "   ${CYAN}app.include_router(${FILE_NAME}.router, prefix=\"/api/v1\", tags=[\"${ENDPOINT_NAME}\"])${NC}"
echo ""
echo "2. أعد بناء الـ Docker image:"
echo -e "   ${CYAN}cd $PROJECT_DIR && docker-compose build api${NC}"
echo ""
if [ "$FULL_CRUD" = true ]; then
    echo "3. قم بتشغيل الـ migration:"
    echo -e "   ${CYAN}cd $BACKEND_DIR && alembic upgrade head${NC}"
    echo ""
fi
echo "4. اختبر الـ endpoint:"
echo -e "   ${CYAN}curl http://localhost:8000/api/v1/$ENDPOINT_NAME${NC}"
echo ""

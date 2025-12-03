#!/bin/bash
# =============================================================================
# Sahool Yemen - سكريبت اختبار الإصلاحات
# Test Script for CI/CD and Model Fixes
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Sahool Yemen - Test Script for Fixes                   ║${NC}"
echo -e "${BLUE}║        سكريبت اختبار إصلاحات منصة سهول اليمن                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${YELLOW}[1/6] Installing dependencies...${NC}"
echo "تثبيت المتطلبات..."
pip install -e libs-shared/ -q
pip install pytest pytest-cov pytest-asyncio python-jose passlib email-validator -q

echo ""
echo -e "${YELLOW}[2/6] Verifying Python syntax...${NC}"
echo "التحقق من صحة Python..."

python -m py_compile libs-shared/sahool_shared/auth/__init__.py && echo -e "  ${GREEN}✅ auth/__init__.py${NC}"
python -m py_compile libs-shared/sahool_shared/auth/password.py && echo -e "  ${GREEN}✅ auth/password.py${NC}"
python -m py_compile libs-shared/sahool_shared/models/alert.py && echo -e "  ${GREEN}✅ models/alert.py${NC}"
python -m py_compile libs-shared/sahool_shared/models/plant_health.py && echo -e "  ${GREEN}✅ models/plant_health.py${NC}"
python -m py_compile libs-shared/tests/test_auth.py && echo -e "  ${GREEN}✅ tests/test_auth.py${NC}"

echo ""
echo -e "${YELLOW}[3/6] Verifying YAML syntax...${NC}"
echo "التحقق من صحة YAML..."
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" && echo -e "  ${GREEN}✅ deploy.yml${NC}"

echo ""
echo -e "${YELLOW}[4/6] Verifying needs_rehash export...${NC}"
echo "التحقق من تصدير needs_rehash..."
python -c "
from sahool_shared.auth.password import needs_rehash
print('  needs_rehash function:', needs_rehash)
" && echo -e "  ${GREEN}✅ needs_rehash exported correctly${NC}"

echo ""
echo -e "${YELLOW}[5/6] Verifying metadata renamed to extra_data...${NC}"
echo "التحقق من تغيير metadata إلى extra_data..."
if grep -q "extra_data" libs-shared/sahool_shared/models/alert.py; then
    echo -e "  ${GREEN}✅ alert.py: extra_data found${NC}"
else
    echo -e "  ${RED}❌ alert.py: extra_data NOT found${NC}"
    exit 1
fi

if grep -q "extra_data" libs-shared/sahool_shared/models/plant_health.py; then
    echo -e "  ${GREEN}✅ plant_health.py: extra_data found${NC}"
else
    echo -e "  ${RED}❌ plant_health.py: extra_data NOT found${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[6/6] Running tests...${NC}"
echo "تشغيل الاختبارات..."
python -m pytest libs-shared/tests/ -v --tb=short 2>&1 | tail -30

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Test Complete! ✅                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"

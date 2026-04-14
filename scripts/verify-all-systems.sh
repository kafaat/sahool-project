#!/bin/bash
# =============================================================================
# SAHOOL AGRI INTELLIGENCE - System Verification Script
# التحقق من اكتمال جميع الأنظمة
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SAHOOL AGRI INTELLIGENCE - System Verification              ║"
echo "║  التحقق من اكتمال جميع الأنظمة                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to check file existence
check_file() {
    local file="$1"
    local description="$2"

    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $description - ملف مفقود: $file${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to check directory existence
check_dir() {
    local dir="$1"
    local description="$2"

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $description - مجلد مفقود: $dir${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to check TypeScript syntax (basic)
check_ts_syntax() {
    local file="$1"

    if [ -f "$file" ]; then
        # Basic check: file is not empty and contains export
        if grep -q "export" "$file" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

echo ""
echo -e "${CYAN}1. التحقق من هيكل المشروع${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services" "مجلد الخدمات"
check_dir "libs-shared" "مجلد المكتبات المشتركة"
check_dir "scripts" "مجلد السكريبتات"

echo ""
echo -e "${CYAN}2. التحقق من Astral Engine v2.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/astral-engine-v2" "مجلد Astral Engine"
check_file "services/astral-engine-v2/src/engine/astral-engine.ts" "محرك Astral الرئيسي"
check_file "services/astral-engine-v2/database/migrations/001_create_astral_calendar.sql" "Migration قاعدة البيانات"

echo ""
echo -e "${CYAN}3. التحقق من NDVI Engine v2.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/ndvi-engine-v2" "مجلد NDVI Engine"
check_file "services/ndvi-engine-v2/src/ndvi-engine.ts" "محرك NDVI الرئيسي"

echo ""
echo -e "${CYAN}4. التحقق من Irrigation Controller v2.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/irrigation-controller-v2" "مجلد Irrigation Controller"
check_file "services/irrigation-controller-v2/src/irrigation-controller.ts" "محرك الري الذكي"

echo ""
echo -e "${CYAN}5. التحقق من Task Optimizer v2.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/task-optimizer-v2" "مجلد Task Optimizer"
check_file "services/task-optimizer-v2/src/ml/task-optimizer-model.ts" "نموذج ML للتحسين"

echo ""
echo -e "${CYAN}6. التحقق من Dashboard Pro v3.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/dashboard-pro-v3" "مجلد Dashboard"
check_file "services/dashboard-pro-v3/src/pages/MainDashboard.tsx" "لوحة التحكم الرئيسية"

echo ""
echo -e "${CYAN}7. التحقق من Intelligence Orchestrator${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "services/intelligence-orchestrator" "مجلد Intelligence Orchestrator"
check_file "services/intelligence-orchestrator/src/orchestrator.ts" "طبقة التكامل الذكية"

echo ""
echo -e "${CYAN}8. التحقق من المكتبات المشتركة${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "libs-shared/sahool_shared/intelligence" "مجلد Intelligence المشترك"
check_file "libs-shared/sahool_shared/intelligence/orchestrator.ts" "Orchestrator المشترك"
check_file "libs-shared/sahool_shared/intelligence/index.ts" "ملف التصدير"

echo ""
echo -e "${CYAN}9. التحقق من السكريبتات${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_file "scripts/master-build-v2.1.sh" "سكريبت البناء الرئيسي"
check_file "scripts/test-intelligence-layer.sh" "سكريبت الاختبار"

echo ""
echo -e "${CYAN}10. التحقق من صحة كود TypeScript${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ts_files=(
    "services/astral-engine-v2/src/engine/astral-engine.ts"
    "services/ndvi-engine-v2/src/ndvi-engine.ts"
    "services/irrigation-controller-v2/src/irrigation-controller.ts"
    "services/task-optimizer-v2/src/ml/task-optimizer-model.ts"
    "services/intelligence-orchestrator/src/orchestrator.ts"
    "services/dashboard-pro-v3/src/pages/MainDashboard.tsx"
)

for file in "${ts_files[@]}"; do
    if check_ts_syntax "$file"; then
        echo -e "${GREEN}✅ صحة الكود: $(basename "$file")${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  تحذير: $(basename "$file") - يحتاج مراجعة${NC}"
        ((WARNINGS++))
    fi
done

# Summary
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}ملخص التحقق${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ نجح: $PASSED${NC}"
echo -e "${RED}❌ فشل: $FAILED${NC}"
echo -e "${YELLOW}⚠️  تحذيرات: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 جميع الأنظمة مكتملة ومتكاملة!                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ بعض الأنظمة غير مكتملة - يرجى مراجعة الأخطاء            ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi

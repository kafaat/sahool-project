#!/bin/bash
#===============================================================================
# Field Suite - سكريبت النشر الرئيسي
# يستنسخ المشروع ويشغله تلقائياً
#===============================================================================

set -e  # التوقف عند أول خطأ

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🚀 Field Suite - Deployment Script${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

#-------------------------------------------------------------------------------
# 1️⃣ التحقق من المتطلبات المسبقة
#-------------------------------------------------------------------------------
echo -e "${BLUE}📋 التحقق من المتطلبات...${NC}"

# فحص git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git غير مثبت${NC}"
    echo "   تثبيت: sudo apt install git"
    exit 1
fi

# فحص Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker غير مثبت${NC}"
    echo "   تثبيت: https://docs.docker.com/get-docker/"
    exit 1
fi

# فحص Docker Compose (v1 أو v2)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ docker-compose غير مثبت${NC}"
    exit 1
fi

# فحص أن Docker يعمل
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon غير يعمل${NC}"
    echo "   تشغيل: sudo systemctl start docker"
    exit 1
fi

echo -e "${GREEN}✅ جميع المتطلبات متوفرة${NC}"
echo ""

#-------------------------------------------------------------------------------
# 2️⃣ استنساخ المشروع
#-------------------------------------------------------------------------------
REPO_URL="https://github.com/kafaat/sahool-project.git"
REPO_DIR="sahool-project"

if [ ! -d "$REPO_DIR" ]; then
    echo -e "${BLUE}📥 استنساخ المشروع...${NC}"
    git clone "$REPO_URL"
    echo -e "${GREEN}✅ تم الاستنساخ بنجاح${NC}"
else
    echo -e "${YELLOW}⚠️  المجلد موجود، تحديث المشروع...${NC}"
    cd "$REPO_DIR"
    git fetch --all
    cd ..
fi

cd "$REPO_DIR"

#-------------------------------------------------------------------------------
# 3️⃣ اختيار الفرع
#-------------------------------------------------------------------------------
MAIN_BRANCH="claude/field-suite-project-generator-013fvPafsGBgXYCqA4RGreZ3"

echo -e "${BLUE}🌿 التبديل إلى الفرع...${NC}"

# محاولة checkout الفرع
if git show-ref --verify --quiet "refs/remotes/origin/$MAIN_BRANCH"; then
    git checkout "$MAIN_BRANCH" 2>/dev/null || git checkout -b "$MAIN_BRANCH" "origin/$MAIN_BRANCH"
    echo -e "${GREEN}✅ تم التبديل للفرع${NC}"
else
    echo -e "${RED}❌ الفرع غير موجود${NC}"
    exit 1
fi

#-------------------------------------------------------------------------------
# 4️⃣ اختيار نوع المشروع
#-------------------------------------------------------------------------------
echo ""
echo "اختر نوع المشروع:"
echo -e "  ${GREEN}1)${NC} 🌾 Full Project (Backend + Web + Mobile)"
echo -e "  ${GREEN}2)${NC} 🛰️  NDVI Project (Satellite Analysis)"
echo ""
read -p "أدخل اختيارك (1 أو 2): " choice

case $choice in
    1)
        PROJECT_DIR="field_suite_full_project"
        PROJECT_NAME="Field Suite Full"
        ;;
    2)
        PROJECT_DIR="field_suite_ndvi_project"
        PROJECT_NAME="Field Suite NDVI"
        ;;
    *)
        echo -e "${RED}❌ خيار غير صالح${NC}"
        exit 1
        ;;
esac

#-------------------------------------------------------------------------------
# 5️⃣ التحقق من ملفات المشروع
#-------------------------------------------------------------------------------
if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    echo -e "${RED}❌ ملف docker-compose.yml غير موجود في $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✅ دخول مجلد: $PROJECT_DIR${NC}"

#-------------------------------------------------------------------------------
# 6️⃣ إعداد ملف البيئة
#-------------------------------------------------------------------------------
ENV_EXAMPLE=""
if [ -f "backend/.env.example" ]; then
    ENV_EXAMPLE="backend/.env.example"
elif [ -f ".env.example" ]; then
    ENV_EXAMPLE=".env.example"
fi

if [ ! -f ".env" ] && [ -n "$ENV_EXAMPLE" ]; then
    echo -e "${YELLOW}⚠️  إنشاء ملف .env من النموذج...${NC}"
    cp "$ENV_EXAMPLE" .env
    echo -e "${GREEN}✅ تم إنشاء .env${NC}"
    echo ""
    echo -e "${YELLOW}🔧 يُنصح بمراجعة وتعديل ملف .env${NC}"
    read -p "هل تريد المتابعة الآن؟ (y/n): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "قم بتعديل .env ثم أعد تشغيل السكريبت"
        exit 0
    fi
fi

#-------------------------------------------------------------------------------
# 7️⃣ بناء وتشغيل المشروع
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🔨 بناء Docker images...${NC}"
$COMPOSE_CMD build --no-cache

echo ""
echo -e "${BLUE}🚀 تشغيل المشروع...${NC}"
$COMPOSE_CMD up -d

#-------------------------------------------------------------------------------
# 8️⃣ انتظار بدء الخدمات
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}⏳ انتظار بدء الخدمات...${NC}"

# تحديد المنفذ حسب المشروع
if [ "$choice" = "1" ]; then
    BACKEND_PORT=8000
    WEB_PORT=3000
else
    BACKEND_PORT=8000
    WEB_PORT=5173
fi

# انتظار Backend
echo -n "   Backend (port $BACKEND_PORT): "
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ جاهز${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
if [ $i -eq 30 ]; then
    echo -e "${YELLOW}⏳ قد يحتاج وقت إضافي${NC}"
fi

# انتظار Web
echo -n "   Web (port $WEB_PORT): "
for i in {1..20}; do
    if curl -s "http://localhost:$WEB_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ جاهز${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

#-------------------------------------------------------------------------------
# 9️⃣ عرض النتائج
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📊 حالة الخدمات:${NC}"
$COMPOSE_CMD ps

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🌐 روابط الوصول - $PROJECT_NAME${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$choice" = "1" ]; then
    echo "   📱 Web Frontend:    http://localhost:3000"
    echo "   🔌 API Backend:     http://localhost:8000"
    echo "   📚 API Docs:        http://localhost:8000/docs"
    echo "   ❤️  Health Check:   http://localhost:8000/health/live"
else
    echo "   📱 Web Frontend:    http://localhost:5173"
    echo "   🔌 API Backend:     http://localhost:8000"
    echo "   📚 API Docs:        http://localhost:8000/docs"
    echo "   🌐 Nginx Proxy:     http://localhost:8080"
    echo "   🗄️  PostgreSQL:     localhost:5432"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ تم الانتهاء بنجاح!${NC}"
echo ""
echo "أوامر مفيدة:"
echo "   $COMPOSE_CMD logs -f        # متابعة السجلات"
echo "   $COMPOSE_CMD ps             # حالة الخدمات"
echo "   $COMPOSE_CMD down           # إيقاف الخدمات"
echo "   $COMPOSE_CMD restart        # إعادة التشغيل"
echo ""

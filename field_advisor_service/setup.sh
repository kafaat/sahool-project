#!/bin/bash
#===============================================================================
# Field Advisor Service - سكريبت الإعداد والتشغيل
#===============================================================================

set -e

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🧠 Field Advisor Service - Smart Agricultural Advisory${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

#-------------------------------------------------------------------------------
# التحقق من المتطلبات
#-------------------------------------------------------------------------------
log_info "التحقق من المتطلبات..."

if ! command -v docker &> /dev/null; then
    log_error "Docker غير مثبت!"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon غير يعمل!"
    exit 1
fi

# فحص Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    log_error "docker-compose غير مثبت!"
    exit 1
fi

log_success "جميع المتطلبات متوفرة"

#-------------------------------------------------------------------------------
# إعداد ملف البيئة
#-------------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "تم إنشاء ملف .env"
    fi
else
    log_success "ملف .env موجود"
fi

#-------------------------------------------------------------------------------
# خيارات التشغيل
#-------------------------------------------------------------------------------
echo ""
echo "اختر طريقة التشغيل:"
echo -e "  ${GREEN}1)${NC} 🚀 تشغيل سريع"
echo -e "  ${GREEN}2)${NC} 🔨 بناء جديد (بدون cache)"
echo -e "  ${GREEN}3)${NC} 🛑 إيقاف الخدمات"
echo -e "  ${GREEN}4)${NC} 📊 عرض الحالة"
echo -e "  ${GREEN}5)${NC} 📝 عرض السجلات"
echo -e "  ${GREEN}6)${NC} 🧹 تنظيف كامل"
echo ""
read -p "اختيارك (1-6): " choice

case $choice in
    1)
        log_info "تشغيل الخدمات..."
        $COMPOSE_CMD up -d
        ;;
    2)
        log_info "بناء وتشغيل الخدمات..."
        $COMPOSE_CMD build --no-cache
        $COMPOSE_CMD up -d
        ;;
    3)
        log_info "إيقاف الخدمات..."
        $COMPOSE_CMD down
        log_success "تم الإيقاف"
        exit 0
        ;;
    4)
        log_info "حالة الخدمات:"
        $COMPOSE_CMD ps
        exit 0
        ;;
    5)
        log_info "السجلات:"
        $COMPOSE_CMD logs --tail=50 -f
        exit 0
        ;;
    6)
        log_warning "هل أنت متأكد؟ (y/n)"
        read -p "" confirm
        if [ "$confirm" = "y" ]; then
            $COMPOSE_CMD down -v --rmi all
            log_success "تم التنظيف"
        fi
        exit 0
        ;;
    *)
        log_error "خيار غير صالح"
        exit 1
        ;;
esac

#-------------------------------------------------------------------------------
# انتظار الخدمات
#-------------------------------------------------------------------------------
echo ""
log_info "انتظار بدء الخدمات..."

echo -n "   Field Advisor API: "
for i in {1..30}; do
    if curl -s http://localhost:8001/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}جاهز${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo -n "   PostgreSQL: "
for i in {1..20}; do
    if docker exec advisor-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}جاهز${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo -n "   Redis: "
for i in {1..10}; do
    if docker exec advisor-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}جاهز${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

#-------------------------------------------------------------------------------
# عرض الحالة والروابط
#-------------------------------------------------------------------------------
echo ""
log_info "حالة الخدمات:"
$COMPOSE_CMD ps

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🌐 روابط الوصول - Field Advisor Service${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "   🔌 API Endpoint:     http://localhost:8001"
echo "   📚 API Docs:         http://localhost:8001/docs"
echo "   📖 ReDoc:            http://localhost:8001/redoc"
echo "   ❤️  Health Check:    http://localhost:8001/health/live"
echo ""
echo "   🗄️  PostgreSQL:      localhost:5433"
echo "   📦 Redis:            localhost:6380"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

log_success "Field Advisor يعمل بنجاح!"
echo ""
echo "أوامر مفيدة:"
echo "   $COMPOSE_CMD logs -f field-advisor   # سجلات API"
echo "   $COMPOSE_CMD ps                      # حالة الخدمات"
echo "   $COMPOSE_CMD down                    # إيقاف"
echo "   ./setup.sh                           # إعادة التشغيل"
echo ""
echo "API Endpoints:"
echo "   POST /advisor/analyze-field          # تحليل الحقل"
echo "   GET  /advisor/recommendations/{id}   # التوصيات"
echo "   GET  /advisor/alerts/{id}            # التنبيهات"
echo "   POST /advisor/playbook               # خطة العمل"
echo ""

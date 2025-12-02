#!/bin/bash
#===============================================================================
# Field Suite NDVI - سكريبت الإعداد والتشغيل
#===============================================================================

set -e

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   🛰️  Field Suite NDVI - Crop Health Analysis Platform"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# التحقق من المتطلبات
log_info "التحقق من المتطلبات..."

if ! command -v docker &> /dev/null; then
    log_error "Docker غير مثبت!"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon غير يعمل!"
    exit 1
fi

log_success "جميع المتطلبات متوفرة"

# إعداد ملف البيئة
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "تم إنشاء ملف .env"
        log_warning "يُنصح بإضافة بيانات Sentinel API في .env"
    fi
else
    log_success "ملف .env موجود"
fi

# خيارات التشغيل
echo ""
echo "اختر طريقة التشغيل:"
echo "  1) 🚀 تشغيل سريع"
echo "  2) 🔨 بناء جديد"
echo "  3) 🛑 إيقاف"
echo "  4) 📊 الحالة"
echo "  5) 📝 السجلات"
echo ""
read -p "اختيارك (1-5): " choice

case $choice in
    1) docker-compose up -d ;;
    2) docker-compose build --no-cache && docker-compose up -d ;;
    3) docker-compose down; exit 0 ;;
    4) docker-compose ps; exit 0 ;;
    5) docker-compose logs --tail=50 -f; exit 0 ;;
    *) log_error "خيار غير صالح"; exit 1 ;;
esac

# انتظار الخدمات
log_info "انتظار بدء الخدمات..."
sleep 10

docker-compose ps

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   🌐 روابط الوصول"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "   📱 Web Frontend:    http://localhost:5173"
echo "   🔌 API Backend:     http://localhost:8000"
echo "   📚 API Docs:        http://localhost:8000/docs"
echo "   🌐 Nginx Proxy:     http://localhost:8080"
echo "   🗄️  PostgreSQL:     localhost:5432"
echo ""
log_success "المشروع يعمل بنجاح!"

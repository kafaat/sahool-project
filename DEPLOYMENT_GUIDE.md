# سهول اليمن - دليل النشر
# Sahool Yemen Field Suite v6.0.0 - Deployment Guide

## نظرة عامة / Overview

سهول اليمن هي منصة زراعية ذكية متكاملة لليمن، توفر تحليلات NDVI، بيانات الطقس، وتوصيات زراعية ذكية.

Sahool Yemen is an integrated smart agricultural platform for Yemen, providing NDVI analytics, weather data, and intelligent farming recommendations.

## المتطلبات / Requirements

- Docker >= 20.10
- Docker Compose >= 2.0
- Git
- 4GB+ RAM
- 20GB+ Disk Space

## التثبيت السريع / Quick Installation

```bash
# 1. Clone the repository
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project

# 2. Make the deployment script executable
chmod +x deploy_sahool_yemen_v6.sh

# 3. Run the deployment script
./deploy_sahool_yemen_v6.sh
```

## التثبيت اليدوي / Manual Installation

```bash
# 1. Copy environment file
cp .env.production.example .env

# 2. Edit environment variables
nano .env

# 3. Build and start services
docker compose -f docker-compose.production.yml up -d --build

# 4. Wait for services to start (about 60 seconds)
sleep 60

# 5. Check service health
docker compose -f docker-compose.production.yml ps
```

## الوصول للخدمات / Service Access

| الخدمة | Service | URL |
|--------|---------|-----|
| المنصة الرئيسية | Main Platform | http://localhost/ |
| API Documentation | وثائق الـ API | http://localhost:8000/docs |
| Prometheus | بروميثيوس | http://localhost:9091 |
| Grafana | جرافانا | http://localhost:3003 |
| Database | قاعدة البيانات | localhost:5434 |
| Redis | ريدس | localhost:6380 |

## البنية المعمارية / Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Gateway (NGINX)                       │
│                         Port 80/443                          │
└────────────────┬────────────────────────────────┬───────────┘
                 │                                │
    ┌────────────▼────────────┐     ┌────────────▼────────────┐
    │      Frontend           │     │       Backend API       │
    │   (React + Vite)        │     │   (FastAPI + Python)    │
    │      Port 3000          │     │       Port 8000         │
    └─────────────────────────┘     └───────────┬─────────────┘
                                                │
        ┌───────────────────────────────────────┼───────────────────────────────────────┐
        │                                       │                                       │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  Weather Core │ │  Imagery Core │ │   Geo Core    │ │Analytics Core │ │  Query Core   │ │ Advisor Core  │
│    الطقس      │ │    الصور      │ │   المساحات   │ │   التحليلات   │ │  الاستعلامات  │ │   المستشار    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                                │
        ┌───────────────────────────────────────┴───────────────────────────────────────┐
        │                                                                               │
┌───────▼───────┐                                                       ┌───────────────▼───────────────┐
│ PostgreSQL    │                                                       │            Redis              │
│ + PostGIS     │                                                       │           (Cache)             │
│ Port 5432     │                                                       │         Port 6379             │
└───────────────┘                                                       └───────────────────────────────┘
```

## المحافظات المدعومة / Supported Governorates

جميع المحافظات اليمنية الـ 20:
1. صنعاء (Sanaa)
2. عدن (Aden)
3. تعز (Taiz)
4. حضرموت (Hadramaut)
5. الحديدة (Hudaydah)
6. إب (Ibb)
7. ذمار (Dhamar)
8. شبوة (Shabwah)
9. لحج (Lahij)
10. أبين (Abyan)
11. مأرب (Marib)
12. الجوف (Al Jawf)
13. عمران (Amran)
14. حجة (Hajjah)
15. المحويت (Mahwit)
16. ريمة (Raymah)
17. المهرة (Al Mahrah)
18. سقطرى (Soqatra)
19. البيضاء (Al Bayda)
20. صعدة (Saadah)

## الأوامر المفيدة / Useful Commands

```bash
# إيقاف المنصة / Stop platform
docker compose -f docker-compose.production.yml down

# عرض السجلات / View logs
docker compose -f docker-compose.production.yml logs -f

# عرض سجلات خدمة محددة / View specific service logs
docker compose -f docker-compose.production.yml logs -f field-suite-backend

# نسخ احتياطي لقاعدة البيانات / Database backup
docker exec sahool-fs-postgres pg_dump -U sahool_production_user sahool_yemen_db > backup_$(date +%Y%m%d).sql

# استعادة قاعدة البيانات / Restore database
docker exec -i sahool-fs-postgres psql -U sahool_production_user sahool_yemen_db < backup_file.sql

# إعادة بناء خدمة / Rebuild service
docker compose -f docker-compose.production.yml up -d --build [service_name]
```

## الدعم / Support

للمساعدة أو الإبلاغ عن مشاكل:
- GitHub Issues: https://github.com/kafaat/sahool-project/issues

---

**سهول اليمن** - المنصة الزراعية الذكية لليمن
**Sahool Yemen** - Smart Agricultural Platform for Yemen

© 2024 Sahool Yemen Team

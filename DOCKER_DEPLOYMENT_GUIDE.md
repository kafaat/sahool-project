# Sahool Platform - Docker Deployment Guide
## دليل نشر منصة سهول باستخدام Docker

**Version:** 3.5.0
**Date:** 2025-12-01
**Status:** Production Ready ✅

---

## Table of Contents | جدول المحتويات

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Service Details](#service-details)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Overview | نظرة عامة

This guide provides complete instructions for deploying the Sahool Agricultural Platform using Docker Compose.

### What's Included | ما هو مُضمّن

The platform consists of **7 core services** plus **2 optional management tools**:

**Core Services:**
1. **PostgreSQL** - Main database with PostGIS extension
2. **Redis** - Caching and session storage
3. **IoT Gateway** - IoT device management and MQTT
4. **Gateway Edge** - Legacy API gateway
5. **ML Engine** - Machine learning and NDVI processing
6. **Agent AI** - LangChain-powered AI assistant
7. **Nginx** - Reverse proxy and load balancer

**Management Tools (Optional):**
8. **pgAdmin** - PostgreSQL administration
9. **Redis Commander** - Redis administration

---

## Architecture | البنية المعمارية

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (Port 80)                   │
│              Reverse Proxy & Load Balancer           │
└─────────────┬───────────────┬───────────────────────┘
              │               │
    ┌─────────┴───────┐      │
    │                 │      │
┌───▼─────┐   ┌──────▼───┐  ┌▼─────────┐   ┌──────────┐
│   IoT   │   │ Gateway  │  │ ML Engine │   │ Agent AI │
│ Gateway │   │   Edge   │  │           │   │          │
│ :8000   │   │  :9000   │  │  :8010    │   │  :8002   │
└────┬────┘   └─────┬────┘  └─────┬─────┘   └────┬─────┘
     │              │             │               │
     │         ┌────┴─────────────┴───────────────┘
     │         │
┌────▼─────────▼──┐        ┌──────────┐
│   PostgreSQL    │        │  Redis   │
│   (PostGIS)     │        │  :6379   │
│     :5432       │        └──────────┘
└─────────────────┘
```

### Network Topology | طوبولوجيا الشبكة

- **Network:** sahool-network (172.20.0.0/16)
- **Bridge Driver:** Enables service-to-service communication
- **External Ports:** Only necessary ports exposed to host

---

## Prerequisites | المتطلبات الأساسية

### System Requirements | متطلبات النظام

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB
- OS: Linux, macOS, or Windows with WSL2

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- OS: Ubuntu 22.04 LTS or similar

### Software Requirements | متطلبات البرمجيات

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

**Required Versions:**
- Docker: 20.10+ or newer
- Docker Compose: 2.0+ or newer

---

## Quick Start | البدء السريع

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/sahool-project.git
cd sahool-project
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Important:** Change these values in production:
```env
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
IOT_SECRET_KEY=your_long_random_secret_key
ML_SECRET_KEY=your_ml_secret_key
AI_SECRET_KEY=your_ai_secret_key
OPENAI_API_KEY=sk-your-openai-key  # Optional
```

### Step 3: Start Services

```bash
# Start all core services
docker-compose up -d

# Or start with management tools
docker-compose --profile tools up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Verify Deployment

```bash
# Health check
curl http://localhost/health

# Check individual services
curl http://localhost:8000/health  # IoT Gateway
curl http://localhost:9000/health  # Gateway Edge
curl http://localhost:8010/health  # ML Engine
curl http://localhost:8002/health  # Agent AI
```

---

## Service Details | تفاصيل الخدمات

### 1. PostgreSQL Database

**Image:** `postgis/postgis:15-3.4`
**Port:** 5432
**Data Volume:** `pgdata_sahool`

**Features:**
- PostGIS extension for geospatial data
- Automatic health checks
- Persistent data storage
- UTF-8 encoding

**Access:**
```bash
# Using docker exec
docker exec -it sahool-postgres psql -U postgres -d sahool

# Using pgAdmin (if enabled)
http://localhost:5050
```

### 2. Redis Cache

**Image:** `redis:7-alpine`
**Port:** 6379
**Data Volume:** `redis_data`

**Features:**
- Password protection
- 256MB memory limit
- LRU eviction policy
- Persistent storage

**Access:**
```bash
# Using redis-cli
docker exec -it sahool-redis redis-cli -a your_password

# Using Redis Commander (if enabled)
http://localhost:8081
```

### 3. IoT Gateway

**Build Context:** `./iot-gateway`
**Port:** 8000
**Logs:** `iot_logs`

**Features:**
- FastAPI framework
- MQTT support for IoT devices
- 4 workers (configurable)
- SQL injection protection

**API Endpoints:**
- Health: `http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`
- API: `http://localhost/api/iot/`

### 4. Gateway Edge (Legacy)

**Build Context:** `./multi-repo/gateway-edge`
**Port:** 9000

**Features:**
- Legacy API support
- Database integration
- Service orchestration

**API Endpoints:**
- Health: `http://localhost:9000/health`
- API: `http://localhost/api/gateway/`

### 5. ML Engine

**Build Context:** `./multi-repo/ml-engine`
**Port:** 8010
**Volumes:** `ml_models`, `ml_cache`, `ml_logs`

**Features:**
- NDVI processing
- Crop disease detection
- Yield prediction
- Model caching

**Resources:**
- CPU Limit: 2 cores
- RAM Limit: 4 GB
- Start Period: 60s

**API Endpoints:**
- Health: `http://localhost:8010/health`
- Predict: `http://localhost/api/ml/predict`

### 6. Agent AI

**Build Context:** `./multi-repo/agent-ai`
**Port:** 8002
**Volumes:** `agent_knowledge`, `agent_cache`, `ai_logs`

**Features:**
- LangChain integration
- RAG (Retrieval-Augmented Generation)
- Cost control ($10/day, $300/month)
- Vector database (ChromaDB)

**Resources:**
- CPU Limit: 1.5 cores
- RAM Limit: 3 GB
- Start Period: 60s

**API Endpoints:**
- Health: `http://localhost:8002/health`
- Chat: `http://localhost/api/ai/chat`

### 7. Nginx Reverse Proxy

**Image:** `nginx:alpine`
**Ports:** 80 (HTTP), 443 (HTTPS)
**Config:** `./nginx/nginx.conf`

**Features:**
- Load balancing
- Rate limiting (10 req/s for API, 100 req/s general)
- Gzip compression
- Security headers
- Custom error pages

**Route Mappings:**
- `/` → Gateway Edge
- `/api/iot/` → IoT Gateway
- `/api/gateway/` → Gateway Edge
- `/api/ml/` → ML Engine
- `/api/ai/` → Agent AI

---

## Configuration | التكوين

### Environment Variables | متغيرات البيئة

All configuration is managed through the `.env` file:

```env
# Database
POSTGRES_DB=sahool
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=redis_password
REDIS_PORT=6379

# Service Ports
IOT_GATEWAY_PORT=8000
GATEWAY_EDGE_PORT=9000
ML_ENGINE_PORT=8010
AGENT_AI_PORT=8002

# Security Keys (CHANGE IN PRODUCTION!)
IOT_SECRET_KEY=change-me-iot
ML_SECRET_KEY=change-me-ml
AI_SECRET_KEY=change-me-ai

# OpenAI (Optional)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-3.5-turbo
MAX_DAILY_COST=10.0
MAX_MONTHLY_COST=300.0

# Logging
LOG_LEVEL=INFO

# Workers
IOT_WORKERS=4
ML_MAX_WORKERS=4
```

### Resource Limits | حدود الموارد

Modify in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

---

## Deployment | النشر

### Development Deployment

```bash
# Start with hot-reload
docker-compose up

# Rebuild after code changes
docker-compose up --build

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build and start in detached mode
docker-compose up -d --build

# Scale specific services
docker-compose up -d --scale iot-gateway=3

# Update a single service
docker-compose up -d --no-deps --build iot-gateway

# Restart all services
docker-compose restart
```

### SSL/TLS Configuration

1. **Generate SSL certificates:**

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/sahool.key \
  -out nginx/ssl/sahool.crt
```

2. **Update nginx/conf.d/ssl.conf:**

```nginx
server {
    listen 443 ssl http2;
    server_name sahool.example.com;

    ssl_certificate /etc/nginx/ssl/sahool.crt;
    ssl_certificate_key /etc/nginx/ssl/sahool.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Include locations from default.conf
    include /etc/nginx/conf.d/locations/*.conf;
}
```

---

## Monitoring | المراقبة

### Container Health

```bash
# Check all container status
docker-compose ps

# View resource usage
docker stats

# Check specific service logs
docker-compose logs -f iot-gateway
docker-compose logs -f ml-engine

# Follow all logs
docker-compose logs -f --tail=100
```

### Database Monitoring

```bash
# Connect to PostgreSQL
docker exec -it sahool-postgres psql -U postgres -d sahool

# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Check database size
SELECT pg_size_pretty(pg_database_size('sahool'));
```

### Redis Monitoring

```bash
# Connect to Redis
docker exec -it sahool-redis redis-cli -a your_password

# Check memory usage
INFO memory

# Check connected clients
INFO clients
```

---

## Troubleshooting | استكشاف الأخطاء

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
docker-compose logs service-name

# Check dependencies
docker-compose ps

# Restart service
docker-compose restart service-name

# Force rebuild
docker-compose up -d --force-recreate --build service-name
```

#### 2. Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker exec sahool-postgres pg_isready -U postgres

# Reset database (WARNING: DELETES DATA)
docker-compose down -v
docker-compose up -d
```

#### 3. Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
# Or free up memory:
docker system prune -a
```

#### 4. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 PID

# Or change port in .env file
```

---

## Maintenance | الصيانة

### Backup

```bash
# Backup PostgreSQL
docker exec sahool-postgres pg_dump -U postgres sahool > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v pgdata_sahool:/data -v $(pwd):/backup alpine \
  tar czf /backup/pgdata_backup_$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Restore PostgreSQL
cat backup_20251201.sql | docker exec -i sahool-postgres psql -U postgres sahool

# Restore volumes
docker run --rm -v pgdata_sahool:/data -v $(pwd):/backup alpine \
  tar xzf /backup/pgdata_backup_20251201.tar.gz -C /
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Update and restart
docker-compose up -d --build

# Clean old images
docker image prune -a
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: DELETES DATA)
docker-compose down -v

# Clean everything
docker system prune -a --volumes
```

---

## Best Practices | أفضل الممارسات

### Security

1. **Always change default passwords** in `.env`
2. **Use SSL/TLS** in production
3. **Restrict network access** with firewall rules
4. **Regular security updates** for images
5. **Use secrets management** for sensitive data

### Performance

1. **Monitor resource usage** regularly
2. **Scale horizontally** for high traffic
3. **Use caching** effectively (Redis)
4. **Optimize database queries**
5. **Enable gzip compression** in Nginx

### Reliability

1. **Regular backups** (daily recommended)
2. **Health checks** for all services
3. **Proper logging** configuration
4. **Monitoring and alerts** setup
5. **Disaster recovery plan**

---

## Support | الدعم

### Getting Help

- **Documentation:** Check this guide and service-specific READMEs
- **Logs:** Always check logs first: `docker-compose logs -f`
- **Issues:** Report at GitHub repository
- **Community:** Join Discord/Slack channel

### Useful Commands

```bash
# Quick health check all services
docker-compose ps

# Restart all services
docker-compose restart

# View logs for all services
docker-compose logs

# Check Docker disk usage
docker system df

# Monitor live stats
docker stats --no-stream
```

---

## Changelog | سجل التغييرات

### v3.5.0 (2025-12-01)
- ✅ Complete Docker Compose integration
- ✅ Added Redis caching layer
- ✅ Added Nginx reverse proxy
- ✅ Configured health checks for all services
- ✅ Added resource limits and reservations
- ✅ Implemented proper networking
- ✅ Added management tools (pgAdmin, Redis Commander)

---

**Version:** 3.5.0
**Last Updated:** 2025-12-01
**Status:** Production Ready ✅

**تم إنشاء هذا الدليل بعناية لضمان نشر سلس وآمن لمنصة سهول الزراعية**

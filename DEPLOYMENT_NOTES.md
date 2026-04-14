# Sahool Yemen - Deployment Notes v10.0.0
# ملاحظات النشر - سهول اليمن

---

## 📋 System Requirements | متطلبات النظام

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4 GB | 8 GB+ |
| Disk | 25 GB | 50 GB+ |
| CPU | 2 cores | 4 cores+ |
| Docker | 24.0+ | Latest |
| Docker Compose | V2 | V2 |

---

## ✅ What's Implemented | ما تم تنفيذه

### 1. Modular Deployment System (`scripts/deploy/`)
- **00-init.sh**: Directory structure, prerequisites, idempotency
- **01-secrets.sh**: Docker Secrets, TLS certificates, secure password generation
- **02-database.sh**: PostgreSQL 16 + PostGIS, RLS, pgAudit, Alembic migrations
- **03-redis.sh**: Redis 7.2 with ACLs, TLS, rate limiting
- **04-services.sh**: Microservices with rolling updates
- **05-monitoring.sh**: Prometheus, Grafana, Loki, Tempo (full observability)
- **06-gateway.sh**: Nginx with SSL, rate limiting, WebSocket support

### 2. Database Features
- ✅ Multi-tenant with Row Level Security (RLS)
- ✅ 4 database roles: `sahool_app`, `sahool_readonly`, `sahool_migration`, `sahool_monitor`
- ✅ pgAudit for compliance logging
- ✅ PostGIS for geospatial queries
- ✅ Yemen governorates seed data (20 regions)
- ✅ JSONB indexes for metadata queries
- ✅ Composite indexes for common queries

### 3. Authentication & Security
- ✅ JWT with access + refresh tokens
- ✅ bcrypt password hashing
- ✅ Token blacklist support
- ✅ Rate limiting per tenant/IP
- ✅ Docker Secrets (no env vars for secrets)

### 4. Microservices
| Service | Status | Description |
|---------|--------|-------------|
| gateway | ✅ Ready | API Gateway with routing |
| auth | ✅ Ready | Authentication service |
| weather | ✅ Ready | Weather data (demo mode available) |
| ndvi | ✅ Ready | NDVI analysis (demo mode available) |
| geo | ✅ Ready | Geospatial queries |
| alert | ✅ Ready | Alert notifications |
| analytics | ✅ Ready | Data analytics |
| advisor | ✅ Ready | Agricultural recommendations |
| query | ✅ Ready | Natural language queries (AR/EN) |

### 5. Monitoring & Observability
- ✅ 4 Grafana dashboards (NDVI, Weather, Services, Infrastructure)
- ✅ Prometheus metrics with Yemen-specific alerts
- ✅ Loki log aggregation
- ✅ Tempo distributed tracing
- ✅ Alertmanager with webhook support

---

## 🔄 Demo Mode | وضع العرض

Services can run in **demo mode** when external API keys are not configured:

### Weather Service
```bash
# Without API key - returns mock data
OPENWEATHER_API_KEY=  # Empty or not set

# With API key - fetches real data
OPENWEATHER_API_KEY=your_api_key_here
```

### NDVI/Imagery Service
```bash
# Without credentials - returns demo tiles
SENTINEL_HUB_CLIENT_ID=  # Empty or not set

# With credentials - fetches real satellite imagery
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_secret
```

---

## 📝 TODO / Future Improvements | للتنفيذ لاحقاً

### High Priority
- [ ] **TDE (Transparent Data Encryption)**: Currently using `pgcrypto` for field-level encryption. Full TDE requires enterprise PostgreSQL or disk-level encryption.
- [ ] **Service Mesh / mTLS**: Internal services communicate over Docker network. mTLS between services is planned but not implemented.
- [ ] **Kubernetes Deployment**: Current deployment is Docker Compose. K8s manifests need to be created.

### Medium Priority
- [ ] **CI/CD Pipeline**: GitHub Actions workflow for automated testing and deployment
- [ ] **Database Backups**: Automated pg_dump with S3/MinIO storage
- [ ] **Blue-Green Deployment**: Currently using rolling updates
- [ ] **Geographic Fencing**: Restrict API access to Yemen IPs (optional)

### Low Priority
- [ ] **Mobile Push Notifications**: FCM/APNs integration for alerts
- [ ] **SMS Alerts**: Twilio/local SMS gateway integration
- [ ] **Offline Sync**: PWA offline data sync for farmers

---

## 🔐 Security Checklist | قائمة فحص الأمان

Before production deployment, verify:

- [ ] All passwords generated using `openssl rand -base64 32`
- [ ] TLS certificates generated and mounted
- [ ] `.env` files not committed to git
- [ ] Docker secrets used (not env vars) for sensitive data
- [ ] RLS policies enabled on all tenant tables
- [ ] Rate limiting configured at gateway
- [ ] pgAudit logging enabled
- [ ] Grafana admin password changed from default

---

## 🚀 Quick Deployment | النشر السريع

```bash
# 1. Clone repository
git clone https://github.com/kafaat/sahool-project.git
cd sahool-project

# 2. Checkout deployment branch
git checkout claude/fix-deployment-script-01CHVyNoqqt74fyUVw798xsU

# 3. Run deployment
sudo ./scripts/deploy/deploy.sh deploy production

# 4. Verify deployment
sudo ./scripts/deploy/deploy.sh validate

# 5. View status
sudo ./scripts/deploy/deploy.sh status
```

---

## 🔧 Troubleshooting | استكشاف الأخطاء

### Database Connection Failed
```bash
# Check PostgreSQL logs
docker logs sahool-postgres

# Verify connection
docker exec sahool-postgres psql -U sahool_app -d sahool -c "SELECT 1"
```

### Redis Connection Failed
```bash
# Check Redis logs
docker logs sahool-redis

# Test connection (replace with actual password)
docker exec sahool-redis redis-cli --user sahool_app -a <password> PING
```

### Service Not Starting
```bash
# Check service logs
docker logs sahool-<service-name>

# Check health
docker inspect sahool-<service-name> --format='{{.State.Health.Status}}'

# Restart service
docker restart sahool-<service-name>
```

### Rollback Deployment
```bash
# List backups
ls -la /opt/sahool/backups/

# Rollback to specific backup
./scripts/deploy/deploy.sh rollback /opt/sahool/backups/pre_deploy_<timestamp>
```

---

## 📊 Metrics & Alerts | المقاييس والتنبيهات

### Key Metrics Exposed
- `sahool_ndvi_value` - Current NDVI readings
- `sahool_weather_temperature` - Temperature by region
- `http_requests_total` - Request count by service
- `http_request_duration_seconds` - Latency histogram

### Alert Rules
- Service down > 2 minutes → Critical
- Error rate > 5% → Warning
- P95 latency > 2s → Warning
- Disk usage > 85% → Warning
- Memory usage > 85% → Warning

---

## 📞 Support | الدعم

- **Documentation**: `scripts/deploy/README.md`
- **Issues**: https://github.com/kafaat/sahool-project/issues
- **Email**: support@sahool.ye

---

**Version**: 10.0.0
**Last Updated**: December 2024
**Maintained by**: Sahool Yemen Team

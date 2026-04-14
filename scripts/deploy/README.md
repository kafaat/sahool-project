# Sahool Yemen Deployment System v9.0.0
# نظام نشر سهول اليمن

## Overview | نظرة عامة

Enterprise-grade modular deployment system for Sahool Yemen agricultural platform.

نظام نشر احترافي ومودولي لمنصة سهول اليمن الزراعية.

## Quick Start | البدء السريع

```bash
# Full deployment
sudo ./deploy.sh deploy production

# Validate only
sudo ./deploy.sh validate

# Rollback to previous version
sudo ./deploy.sh rollback
```

## Architecture | البنية

```
scripts/deploy/
├── deploy.sh              # Main orchestrator
├── lib/
│   └── common.sh          # Shared utilities
├── modules/
│   ├── 00-init.sh         # Directory structure & prerequisites
│   ├── 01-secrets.sh      # Secrets & TLS certificates
│   ├── 02-database.sh     # PostgreSQL with RLS & pgAudit
│   ├── 03-redis.sh        # Redis with ACLs & TLS
│   ├── 04-services.sh     # Microservices deployment
│   ├── 05-monitoring.sh   # Grafana, Loki, Tempo, Prometheus
│   └── 06-gateway.sh      # Nginx reverse proxy & SSL
└── README.md
```

## Modules | الوحدات

### 00-init.sh - Initialization
- Creates directory structure under `/opt/sahool`
- Sets up permissions and gitignore
- Validates prerequisites (Docker, disk space, memory)

### 01-secrets.sh - Secrets Management
- Generates secure passwords and API keys
- Creates Docker secrets for Swarm mode
- Generates TLS certificates for internal communication
- Creates environment configuration files

### 02-database.sh - PostgreSQL Setup
- PostgreSQL 16 with PostGIS 3.4
- Role-based access control:
  - `sahool_app` - Application user
  - `sahool_readonly` - Analytics read-only
  - `sahool_migration` - Schema migrations
  - `sahool_monitor` - Monitoring access
- Row Level Security (RLS) for multi-tenancy
- pgAudit logging for compliance
- Alembic migration system
- Yemen governorates seed data

### 03-redis.sh - Redis Setup
- Redis 7.2 with persistence
- ACL-based authentication
- TLS encryption support
- Rate limiting configuration
- Prometheus exporter

### 04-services.sh - Microservices
- Service deployment with Docker Compose
- Health checks and resource limits
- Rolling update support
- Zero-downtime deployment

### 05-monitoring.sh - Observability Stack
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization
- **Loki** - Log aggregation
- **Tempo** - Distributed tracing
- **Alertmanager** - Alert routing
- Pre-configured dashboards for Sahool

### 06-gateway.sh - API Gateway
- Nginx reverse proxy
- SSL/TLS termination
- Rate limiting
- WebSocket support
- Custom error pages (Arabic)

## Commands | الأوامر

```bash
# Deploy to production
./deploy.sh deploy production

# Deploy to staging
./deploy.sh deploy staging

# Validate deployment configuration
./deploy.sh validate

# Check service status
./deploy.sh status

# Rollback to specific backup
./deploy.sh rollback 20241203_120000

# View logs
./deploy.sh logs [service-name]

# Backup current state
./deploy.sh backup
```

## Environment Variables | متغيرات البيئة

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_DIR` | `/opt/sahool` | Base project directory |
| `DATA_DIR` | `/opt/sahool/data` | Data storage directory |
| `SECRETS_DIR` | `/opt/sahool/secrets` | Secrets directory |
| `SAHOOL_DOMAIN` | `sahool.local` | Domain name |
| `POSTGRES_VERSION` | `16` | PostgreSQL version |
| `REDIS_VERSION` | `7.2` | Redis version |
| `FORCE_REINIT` | `false` | Force reinitialization |
| `DEBUG` | `false` | Enable debug logging |

## Security Features | ميزات الأمان

1. **Secrets Management**
   - Docker secrets for sensitive data
   - Encrypted files on disk
   - No secrets in environment variables

2. **Database Security**
   - Row Level Security for tenant isolation
   - Separate roles with minimal privileges
   - Audit logging with pgAudit
   - SSL/TLS connections

3. **Network Security**
   - TLS 1.2/1.3 only
   - Rate limiting at gateway
   - Internal network isolation

4. **Authentication**
   - JWT with short-lived access tokens
   - Refresh token rotation
   - bcrypt password hashing

## Backup & Recovery | النسخ الاحتياطي والاستعادة

### Automatic Backups
```bash
# Create manual backup
./deploy.sh backup

# Backups stored in /opt/sahool/backups/
```

### Restore Process
```bash
# List available backups
ls -la /opt/sahool/backups/

# Rollback to specific backup
./deploy.sh rollback 20241203_120000
```

## Monitoring | المراقبة

### Access Dashboards

- **Grafana**: https://grafana.sahool.local (default: admin/admin)
- **Prometheus**: http://localhost:9090 (internal only)

### Key Metrics

- Request rate per service
- Error rate (5xx responses)
- P95 latency
- Database connections
- Redis memory usage
- Container resource usage

### Alerts

Pre-configured alerts for:
- Service down
- High error rate (>5%)
- High latency (>2s P95)
- Database connection issues
- Disk space low (<15%)
- Memory usage high (>85%)

## Troubleshooting | استكشاف الأخطاء

### Service won't start
```bash
# Check logs
docker logs sahool-<service-name>

# Check health status
docker inspect sahool-<service-name> --format='{{.State.Health.Status}}'

# Restart service
docker restart sahool-<service-name>
```

### Database connection issues
```bash
# Test connection
docker exec sahool-postgres psql -U sahool_app -d sahool -c "SELECT 1"

# Check pg_hba.conf
docker exec sahool-postgres cat /var/lib/postgresql/data/pg_hba.conf
```

### Redis connection issues
```bash
# Test connection
docker exec sahool-redis redis-cli --user sahool_app -a <password> PING

# Check ACL
docker exec sahool-redis redis-cli ACL LIST
```

## Development | التطوير

### Local Development
```bash
# Deploy in development mode
ENVIRONMENT=development ./deploy.sh deploy

# Use local Docker Compose
cd /opt/sahool/services/compose
docker compose -f docker-compose.services.yml up -d
```

### Adding New Service
1. Create service directory in `services/<name>/app/`
2. Add Dockerfile in `services/Dockerfile.<name>`
3. Update `04-services.sh` with new service definition
4. Add service to `docker-compose.services.yml`
5. Add Prometheus scrape config in `05-monitoring.sh`

## License | الترخيص

Proprietary - Sahool Yemen © 2024

---

للدعم الفني: support@sahool.ye

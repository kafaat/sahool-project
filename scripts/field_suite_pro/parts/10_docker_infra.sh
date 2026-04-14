#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 10: Docker & Infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء ملفات Docker والبنية التحتية..."

# ─────────────────────────────────────────────────────────────────────────────
# Backend Dockerfile (Multi-stage)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/Dockerfile" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Backend Dockerfile
# Multi-stage build for optimized production image
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Production
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgdal32 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=appuser:appgroup . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Backend Requirements.txt
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/requirements.txt" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Python Dependencies
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Core Framework
# ─────────────────────────────────────────────────────────────────────────────
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
geoalchemy2==0.14.3

# ─────────────────────────────────────────────────────────────────────────────
# Authentication & Security
# ─────────────────────────────────────────────────────────────────────────────
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# ─────────────────────────────────────────────────────────────────────────────
# Cache & Message Queue
# ─────────────────────────────────────────────────────────────────────────────
redis==5.0.1
celery==5.3.6
flower==2.0.1

# ─────────────────────────────────────────────────────────────────────────────
# Geospatial & Image Processing
# ─────────────────────────────────────────────────────────────────────────────
rasterio==1.3.9
numpy==1.26.3
shapely==2.0.2
pyproj==3.6.1
Pillow==10.2.0

# ─────────────────────────────────────────────────────────────────────────────
# HTTP & External APIs
# ─────────────────────────────────────────────────────────────────────────────
httpx==0.26.0
aiofiles==23.2.1

# ─────────────────────────────────────────────────────────────────────────────
# Monitoring & Logging
# ─────────────────────────────────────────────────────────────────────────────
prometheus-client==0.19.0
python-json-logger==2.0.7
structlog==24.1.0

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────
python-dotenv==1.0.0
tenacity==8.2.3
orjson==3.9.12

# ─────────────────────────────────────────────────────────────────────────────
# Testing (Dev only)
# ─────────────────────────────────────────────────────────────────────────────
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
factory-boy==3.3.0
faker==22.2.0
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Celery Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/Dockerfile.celery" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Celery Worker Dockerfile
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgdal32 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Create directories
RUN mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appgroup /app

USER appuser

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Default command - worker
CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Frontend Dockerfile (Multi-stage)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/frontend/Dockerfile" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Frontend Dockerfile
# Multi-stage build for optimized production image
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Production with Nginx
# ─────────────────────────────────────────────────────────────────────────────
FROM nginx:alpine as production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Nginx Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/frontend/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Docker Compose - Development
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/docker-compose.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Docker Compose (Development)
# ═══════════════════════════════════════════════════════════════════════════════

version: '3.8'

services:
  # ─────────────────────────────────────────────────────────────────────────────
  # PostgreSQL with PostGIS
  # ─────────────────────────────────────────────────────────────────────────────
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: field_suite_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-field_suite_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_network

  # ─────────────────────────────────────────────────────────────────────────────
  # Redis
  # ─────────────────────────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: field_suite_redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_network

  # ─────────────────────────────────────────────────────────────────────────────
  # Backend API
  # ─────────────────────────────────────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: field_suite_backend
    environment:
      - ENV=development
      - DEBUG=true
      - POSTGRES_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - upload_data:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - field_suite_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # ─────────────────────────────────────────────────────────────────────────────
  # Celery Worker
  # ─────────────────────────────────────────────────────────────────────────────
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    container_name: field_suite_celery_worker
    environment:
      - ENV=development
      - POSTGRES_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - upload_data:/app/uploads
    depends_on:
      - backend
      - redis
    networks:
      - field_suite_network
    command: celery -A app.tasks.celery_app worker --loglevel=info

  # ─────────────────────────────────────────────────────────────────────────────
  # Celery Beat (Scheduler)
  # ─────────────────────────────────────────────────────────────────────────────
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    container_name: field_suite_celery_beat
    environment:
      - ENV=development
      - POSTGRES_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      - celery_worker
    networks:
      - field_suite_network
    command: celery -A app.tasks.celery_app beat --loglevel=info

  # ─────────────────────────────────────────────────────────────────────────────
  # Flower (Celery Monitoring)
  # ─────────────────────────────────────────────────────────────────────────────
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    container_name: field_suite_flower
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    ports:
      - "5555:5555"
    depends_on:
      - celery_worker
    networks:
      - field_suite_network
    command: celery -A app.tasks.celery_app flower --port=5555

  # ─────────────────────────────────────────────────────────────────────────────
  # Frontend
  # ─────────────────────────────────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: builder
    container_name: field_suite_frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    networks:
      - field_suite_network
    command: npm run dev -- --host

  # ─────────────────────────────────────────────────────────────────────────────
  # Prometheus (Metrics)
  # ─────────────────────────────────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: field_suite_prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - field_suite_network
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'

  # ─────────────────────────────────────────────────────────────────────────────
  # Grafana (Dashboards)
  # ─────────────────────────────────────────────────────────────────────────────
  grafana:
    image: grafana/grafana:10.2.2
    container_name: field_suite_grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - field_suite_network

# ─────────────────────────────────────────────────────────────────────────────
# Networks
# ─────────────────────────────────────────────────────────────────────────────
networks:
  field_suite_network:
    driver: bridge

# ─────────────────────────────────────────────────────────────────────────────
# Volumes
# ─────────────────────────────────────────────────────────────────────────────
volumes:
  postgres_data:
  redis_data:
  upload_data:
  prometheus_data:
  grafana_data:
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Docker Compose - Production
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/docker-compose.prod.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Docker Compose (Production)
# ═══════════════════════════════════════════════════════════════════════════════

version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: field_suite_postgres_prod
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'

  redis:
    image: redis:7-alpine
    container_name: field_suite_redis_prod
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  backend:
    image: ${DOCKER_REGISTRY}/field-suite-backend:${VERSION:-latest}
    container_name: field_suite_backend_prod
    environment:
      - ENV=production
      - DEBUG=false
    env_file:
      - .env.production
    volumes:
      - upload_data:/app/uploads
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - field_suite_network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1'
      update_config:
        parallelism: 1
        delay: 10s
      rollback_config:
        parallelism: 1

  celery_worker:
    image: ${DOCKER_REGISTRY}/field-suite-backend:${VERSION:-latest}
    container_name: field_suite_celery_worker_prod
    env_file:
      - .env.production
    volumes:
      - upload_data:/app/uploads
    restart: always
    networks:
      - field_suite_network
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '2'

  celery_beat:
    image: ${DOCKER_REGISTRY}/field-suite-backend:${VERSION:-latest}
    container_name: field_suite_celery_beat_prod
    env_file:
      - .env.production
    restart: always
    networks:
      - field_suite_network
    command: celery -A app.tasks.celery_app beat --loglevel=info
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'

  frontend:
    image: ${DOCKER_REGISTRY}/field-suite-frontend:${VERSION:-latest}
    container_name: field_suite_frontend_prod
    restart: always
    networks:
      - field_suite_network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 128M
          cpus: '0.25'

  nginx:
    image: nginx:alpine
    container_name: field_suite_nginx_prod
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    restart: always
    networks:
      - field_suite_network

networks:
  field_suite_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  upload_data:
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Prometheus Configuration
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_NAME/monitoring/grafana/provisioning/datasources"
mkdir -p "$PROJECT_NAME/monitoring/grafana/provisioning/dashboards"

cat > "$PROJECT_NAME/monitoring/prometheus.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Configuration
# ═══════════════════════════════════════════════════════════════════════════════

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files: []

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Grafana Datasource
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/monitoring/grafana/provisioning/datasources/datasources.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Kubernetes Manifests
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_NAME/k8s/base"
mkdir -p "$PROJECT_NAME/k8s/overlays/development"
mkdir -p "$PROJECT_NAME/k8s/overlays/production"

# Namespace
cat > "$PROJECT_NAME/k8s/base/namespace.yaml" << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: field-suite
  labels:
    app: field-suite
EOF

# ConfigMap
cat > "$PROJECT_NAME/k8s/base/configmap.yaml" << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: field-suite-config
  namespace: field-suite
data:
  APP_NAME: "Field Suite Pro"
  ENV: "production"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  ENABLE_METRICS: "true"
  ENABLE_WEBSOCKET: "true"
EOF

# Secret (template)
cat > "$PROJECT_NAME/k8s/base/secret.yaml" << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: field-suite-secrets
  namespace: field-suite
type: Opaque
stringData:
  SECRET_KEY: "CHANGE_ME_IN_PRODUCTION"
  POSTGRES_PASSWORD: "CHANGE_ME_IN_PRODUCTION"
  REDIS_PASSWORD: "CHANGE_ME_IN_PRODUCTION"
EOF

# Backend Deployment
cat > "$PROJECT_NAME/k8s/base/backend-deployment.yaml" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: field-suite-backend
  namespace: field-suite
  labels:
    app: field-suite
    component: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: field-suite
      component: backend
  template:
    metadata:
      labels:
        app: field-suite
        component: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: backend
          image: field-suite-backend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: field-suite-config
            - secretRef:
                name: field-suite-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: uploads
              mountPath: /app/uploads
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: field-suite-uploads-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: field-suite-backend
  namespace: field-suite
spec:
  selector:
    app: field-suite
    component: backend
  ports:
    - port: 8000
      targetPort: 8000
      name: http
  type: ClusterIP
EOF

# Frontend Deployment
cat > "$PROJECT_NAME/k8s/base/frontend-deployment.yaml" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: field-suite-frontend
  namespace: field-suite
  labels:
    app: field-suite
    component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: field-suite
      component: frontend
  template:
    metadata:
      labels:
        app: field-suite
        component: frontend
    spec:
      containers:
        - name: frontend
          image: field-suite-frontend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 80
              name: http
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: field-suite-frontend
  namespace: field-suite
spec:
  selector:
    app: field-suite
    component: frontend
  ports:
    - port: 80
      targetPort: 80
      name: http
  type: ClusterIP
EOF

# Celery Worker Deployment
cat > "$PROJECT_NAME/k8s/base/celery-deployment.yaml" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: field-suite-celery-worker
  namespace: field-suite
  labels:
    app: field-suite
    component: celery-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: field-suite
      component: celery-worker
  template:
    metadata:
      labels:
        app: field-suite
        component: celery-worker
    spec:
      containers:
        - name: celery-worker
          image: field-suite-backend:latest
          imagePullPolicy: Always
          command: ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
          envFrom:
            - configMapRef:
                name: field-suite-config
            - secretRef:
                name: field-suite-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          volumeMounts:
            - name: uploads
              mountPath: /app/uploads
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: field-suite-uploads-pvc
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: field-suite-celery-beat
  namespace: field-suite
  labels:
    app: field-suite
    component: celery-beat
spec:
  replicas: 1
  selector:
    matchLabels:
      app: field-suite
      component: celery-beat
  template:
    metadata:
      labels:
        app: field-suite
        component: celery-beat
    spec:
      containers:
        - name: celery-beat
          image: field-suite-backend:latest
          imagePullPolicy: Always
          command: ["celery", "-A", "app.tasks.celery_app", "beat", "--loglevel=info"]
          envFrom:
            - configMapRef:
                name: field-suite-config
            - secretRef:
                name: field-suite-secrets
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
EOF

# Ingress
cat > "$PROJECT_NAME/k8s/base/ingress.yaml" << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: field-suite-ingress
  namespace: field-suite
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  tls:
    - hosts:
        - field-suite.example.com
      secretName: field-suite-tls
  rules:
    - host: field-suite.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: field-suite-backend
                port:
                  number: 8000
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: field-suite-backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: field-suite-frontend
                port:
                  number: 80
EOF

# PersistentVolumeClaim
cat > "$PROJECT_NAME/k8s/base/pvc.yaml" << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: field-suite-uploads-pvc
  namespace: field-suite
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
EOF

# HorizontalPodAutoscaler
cat > "$PROJECT_NAME/k8s/base/hpa.yaml" << 'EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: field-suite-backend-hpa
  namespace: field-suite
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: field-suite-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: field-suite-celery-hpa
  namespace: field-suite
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: field-suite-celery-worker
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
EOF

# Kustomization
cat > "$PROJECT_NAME/k8s/base/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: field-suite

resources:
  - namespace.yaml
  - configmap.yaml
  - secret.yaml
  - pvc.yaml
  - backend-deployment.yaml
  - frontend-deployment.yaml
  - celery-deployment.yaml
  - ingress.yaml
  - hpa.yaml

commonLabels:
  app: field-suite
  version: "2.0.0"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Database Init Script
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_NAME/backend/scripts"

cat > "$PROJECT_NAME/backend/scripts/init-db.sql" << 'EOF'
-- ═══════════════════════════════════════════════════════════════════════════════
-- Field Suite Pro - Database Initialization
-- ═══════════════════════════════════════════════════════════════════════════════

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for common queries (will be created by Alembic)
-- These are just for reference

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE field_suite_db TO postgres;
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Environment Files
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.env.example" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Environment Variables
# ═══════════════════════════════════════════════════════════════════════════════

# Application
APP_NAME=Field Suite Pro
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=field_suite_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External APIs
OPENWEATHER_API_KEY=
SENTINEL_CLIENT_ID=
SENTINEL_CLIENT_SECRET=

# File Upload
MAX_UPLOAD_SIZE_MB=100
UPLOAD_DIR=/tmp/uploads

# Docker Registry (for production)
DOCKER_REGISTRY=ghcr.io/your-org
VERSION=latest
EOF

cat > "$PROJECT_NAME/.env.production.example" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Production Environment Variables
# ═══════════════════════════════════════════════════════════════════════════════

# Application
APP_NAME=Field Suite Pro
ENV=production
DEBUG=false
SECRET_KEY=GENERATE_A_STRONG_SECRET_KEY

# Database
POSTGRES_USER=field_suite_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=field_suite_db

# Redis
REDIS_URL=redis://:REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=STRONG_REDIS_PASSWORD

# Celery
CELERY_BROKER_URL=redis://:REDIS_PASSWORD@redis:6379/1
CELERY_RESULT_BACKEND=redis://:REDIS_PASSWORD@redis:6379/2

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External APIs
OPENWEATHER_API_KEY=your_api_key
SENTINEL_CLIENT_ID=your_client_id
SENTINEL_CLIENT_SECRET=your_client_secret

# File Upload
MAX_UPLOAD_SIZE_MB=100
UPLOAD_DIR=/app/uploads

# Docker Registry
DOCKER_REGISTRY=ghcr.io/your-org
VERSION=latest
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Makefile
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/Makefile" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Makefile
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help dev prod build test clean migrate

# Default target
help:
	@echo "Field Suite Pro - Available Commands"
	@echo "────────────────────────────────────"
	@echo "  make dev        - Start development environment"
	@echo "  make prod       - Start production environment"
	@echo "  make build      - Build Docker images"
	@echo "  make test       - Run tests"
	@echo "  make migrate    - Run database migrations"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make logs       - View logs"
	@echo "  make shell      - Open backend shell"

# Development
dev:
	docker-compose up -d
	@echo "Development environment started!"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Flower:   http://localhost:5555"
	@echo "  Grafana:  http://localhost:3001"

# Production
prod:
	docker-compose -f docker-compose.prod.yml up -d

# Build images
build:
	docker-compose build --no-cache

# Run tests
test:
	docker-compose exec backend pytest -v --cov=app --cov-report=html

# Run migrations
migrate:
	docker-compose exec backend alembic upgrade head

# Create new migration
migration:
	@read -p "Migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

# Clean up
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# View logs
logs:
	docker-compose logs -f

# Backend shell
shell:
	docker-compose exec backend bash

# Frontend shell
shell-frontend:
	docker-compose exec frontend sh

# Database shell
db:
	docker-compose exec postgres psql -U postgres -d field_suite_db

# Redis CLI
redis:
	docker-compose exec redis redis-cli

# Restart services
restart:
	docker-compose restart

# Stop services
stop:
	docker-compose stop

# Status
status:
	docker-compose ps
EOF

log_success "تم إنشاء ملفات Docker والبنية التحتية"

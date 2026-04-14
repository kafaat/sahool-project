#!/bin/bash
# =============================================================================
# Sahool Yemen v9.0.0 - Services Module
# وحدة نشر الخدمات المصغرة
# =============================================================================

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# =============================================================================
# Configuration
# =============================================================================

SERVICES_DIR="${PROJECT_DIR:-/opt/sahool}/services"
COMPOSE_DIR="${SERVICES_DIR}/compose"
REGISTRY="${DOCKER_REGISTRY:-sahool}"

# Service definitions
declare -A SERVICES=(
    ["gateway"]="API Gateway - بوابة API"
    ["auth"]="Authentication Service - خدمة المصادقة"
    ["weather"]="Weather Service - خدمة الطقس"
    ["ndvi"]="NDVI Analysis Service - خدمة تحليل NDVI"
    ["geo"]="Geospatial Service - خدمة البيانات الجغرافية"
    ["alert"]="Alert Service - خدمة التنبيهات"
    ["analytics"]="Analytics Service - خدمة التحليلات"
)

# =============================================================================
# Service Setup Functions
# =============================================================================

setup_services_directories() {
    log_info "Creating services directories..."

    local dirs=(
        "${SERVICES_DIR}"
        "${COMPOSE_DIR}"
        "${SERVICES_DIR}/logs"
        "${SERVICES_DIR}/tmp"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    log_success "Services directories created"
}

create_base_dockerfile() {
    log_info "Creating base Dockerfile..."

    cat > "${SERVICES_DIR}/Dockerfile.base" << 'EOF'
# =============================================================================
# Sahool Yemen Base Service Image v9.0.0
# =============================================================================

FROM python:3.11-slim as base

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 sahool \
    && useradd -u 1000 -g sahool -m -s /bin/bash sahool

WORKDIR /app

# =============================================================================
# Builder Stage
# =============================================================================
FROM base as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install shared library
COPY libs-shared /app/libs-shared
RUN pip install --no-cache-dir /app/libs-shared

# Copy and install service requirements
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# =============================================================================
# Runtime Stage
# =============================================================================
FROM base as runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create app directories
RUN mkdir -p /app/logs /app/tmp && chown -R sahool:sahool /app

# Switch to non-root user
USER sahool

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
EOF

    log_success "Base Dockerfile created"
}

create_service_dockerfile() {
    local service_name="$1"

    log_info "Creating Dockerfile for ${service_name}..."

    cat > "${SERVICES_DIR}/Dockerfile.${service_name}" << EOF
# =============================================================================
# Sahool Yemen ${service_name^} Service v9.0.0
# =============================================================================

FROM ${REGISTRY}/sahool-base:latest

# Copy service code
COPY --chown=sahool:sahool services/${service_name}/app /app/app

# Service-specific configuration
ENV SERVICE_NAME=${service_name}

LABEL org.opencontainers.image.title="Sahool ${service_name^} Service" \\
      org.opencontainers.image.version="9.0.0" \\
      org.opencontainers.image.vendor="Sahool Yemen"
EOF

    log_success "Dockerfile for ${service_name} created"
}

create_docker_compose() {
    log_info "Creating Docker Compose configuration..."

    cat > "${COMPOSE_DIR}/docker-compose.services.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Microservices v9.0.0
# =============================================================================
version: '3.8'

x-service-defaults: &service-defaults
  restart: unless-stopped
  networks:
    - sahool-network
  logging:
    driver: "json-file"
    options:
      max-size: "20m"
      max-file: "5"
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        cpus: '0.1'
        memory: 128M

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

services:
  # =========================================================================
  # API Gateway
  # =========================================================================
  gateway:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-gateway:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.gateway
    container_name: sahool-gateway
    ports:
      - "8080:8000"
    environment:
      - SERVICE_NAME=gateway
      - WEATHER_SERVICE_URL=http://weather:8000
      - NDVI_SERVICE_URL=http://ndvi:8000
      - GEO_SERVICE_URL=http://geo:8000
      - ALERT_SERVICE_URL=http://alert:8000
      - AUTH_SERVICE_URL=http://auth:8000
      - ANALYTICS_SERVICE_URL=http://analytics:8000
      - REDIS_URL=redis://redis:6379
      - RATE_LIMIT_REQUESTS=200
      - RATE_LIMIT_WINDOW=60
    secrets:
      - jwt_secret
      - redis_app_password
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      auth:
        condition: service_healthy
      redis:
        condition: service_healthy

  # =========================================================================
  # Authentication Service
  # =========================================================================
  auth:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-auth:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.auth
    container_name: sahool-auth
    environment:
      - SERVICE_NAME=auth
      - DATABASE_URL=postgresql+asyncpg://sahool_app:${DB_APP_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
      - JWT_ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - REFRESH_TOKEN_EXPIRE_DAYS=7
    secrets:
      - jwt_secret
      - jwt_refresh_secret
      - db_app_password
      - redis_app_password
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # =========================================================================
  # Weather Service
  # =========================================================================
  weather:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-weather:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.weather
    container_name: sahool-weather
    environment:
      - SERVICE_NAME=weather
      - DATABASE_URL=postgresql+asyncpg://sahool_app:${DB_APP_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
      - OPENWEATHER_API_KEY_FILE=/run/secrets/openweather_api_key
      - CACHE_TTL=1800
    secrets:
      - db_app_password
      - redis_app_password
      - openweather_api_key
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy

  # =========================================================================
  # NDVI Analysis Service
  # =========================================================================
  ndvi:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-ndvi:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.ndvi
    container_name: sahool-ndvi
    environment:
      - SERVICE_NAME=ndvi
      - DATABASE_URL=postgresql+asyncpg://sahool_app:${DB_APP_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
      - SENTINEL_HUB_CLIENT_ID_FILE=/run/secrets/sentinel_hub_client_id
      - SENTINEL_HUB_CLIENT_SECRET_FILE=/run/secrets/sentinel_hub_client_secret
      - CACHE_TTL=3600
    secrets:
      - db_app_password
      - redis_app_password
      - sentinel_hub_client_id
      - sentinel_hub_client_secret
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # =========================================================================
  # Geospatial Service
  # =========================================================================
  geo:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-geo:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.geo
    container_name: sahool-geo
    environment:
      - SERVICE_NAME=geo
      - DATABASE_URL=postgresql+asyncpg://sahool_app:${DB_APP_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
    secrets:
      - db_app_password
      - redis_app_password
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy

  # =========================================================================
  # Alert Service
  # =========================================================================
  alert:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-alert:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.alert
    container_name: sahool-alert
    environment:
      - SERVICE_NAME=alert
      - DATABASE_URL=postgresql+asyncpg://sahool_app:${DB_APP_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
      - TWILIO_ACCOUNT_SID_FILE=/run/secrets/twilio_account_sid
      - TWILIO_AUTH_TOKEN_FILE=/run/secrets/twilio_auth_token
    secrets:
      - db_app_password
      - redis_app_password
      - twilio_account_sid
      - twilio_auth_token
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy

  # =========================================================================
  # Analytics Service
  # =========================================================================
  analytics:
    <<: *service-defaults
    image: ${REGISTRY:-sahool}/sahool-analytics:${VERSION:-latest}
    build:
      context: ../..
      dockerfile: services/Dockerfile.analytics
    container_name: sahool-analytics
    environment:
      - SERVICE_NAME=analytics
      - DATABASE_URL=postgresql+asyncpg://sahool_readonly:${DB_READONLY_PASSWORD}@postgres:5432/sahool
      - REDIS_URL=redis://redis:6379
    secrets:
      - db_readonly_password
      - redis_app_password
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    depends_on:
      postgres:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

networks:
  sahool-network:
    external: true

secrets:
  jwt_secret:
    external: true
  jwt_refresh_secret:
    external: true
  db_app_password:
    external: true
  db_readonly_password:
    external: true
  redis_app_password:
    external: true
  openweather_api_key:
    external: true
  sentinel_hub_client_id:
    external: true
  sentinel_hub_client_secret:
    external: true
  twilio_account_sid:
    external: true
  twilio_auth_token:
    external: true
EOF

    log_success "Docker Compose configuration created"
}

create_env_template() {
    log_info "Creating environment template..."

    cat > "${COMPOSE_DIR}/.env.template" << 'EOF'
# =============================================================================
# Sahool Yemen Services Environment Template
# =============================================================================

# General
VERSION=9.0.0
ENVIRONMENT=production
REGISTRY=sahool

# Database
DB_APP_PASSWORD=<from-secrets>
DB_READONLY_PASSWORD=<from-secrets>

# Redis
REDIS_APP_PASSWORD=<from-secrets>

# JWT
JWT_SECRET=<from-secrets>
JWT_REFRESH_SECRET=<from-secrets>

# External APIs (optional - use secrets in production)
# OPENWEATHER_API_KEY=
# SENTINEL_HUB_CLIENT_ID=
# SENTINEL_HUB_CLIENT_SECRET=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
EOF

    log_success "Environment template created"
}

build_services() {
    log_info "Building service images..."

    local project_root="${PROJECT_DIR:-/opt/sahool}"

    # Build base image first
    log_info "Building base image..."
    docker build \
        -t "${REGISTRY}/sahool-base:latest" \
        -f "${SERVICES_DIR}/Dockerfile.base" \
        "$project_root"

    # Build each service
    for service in "${!SERVICES[@]}"; do
        log_info "Building ${service} service..."

        if [[ -f "${SERVICES_DIR}/Dockerfile.${service}" ]]; then
            docker build \
                -t "${REGISTRY}/sahool-${service}:latest" \
                -t "${REGISTRY}/sahool-${service}:9.0.0" \
                -f "${SERVICES_DIR}/Dockerfile.${service}" \
                "$project_root"
        fi
    done

    log_success "All service images built"
}

start_services() {
    log_info "Starting services..."

    cd "${COMPOSE_DIR}"

    docker compose -f docker-compose.services.yml up -d

    log_success "Services started"
}

stop_services() {
    log_info "Stopping services..."

    cd "${COMPOSE_DIR}"

    docker compose -f docker-compose.services.yml down

    log_success "Services stopped"
}

verify_services() {
    log_info "Verifying services..."

    local errors=0

    # Check if services are running
    for service in "${!SERVICES[@]}"; do
        local container="sahool-${service}"

        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            # Check health
            local health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")

            if [[ "$health" == "healthy" ]]; then
                log_success "${service}: healthy"
            elif [[ "$health" == "starting" ]]; then
                log_warning "${service}: starting..."
            else
                log_error "${service}: ${health}"
                ((errors++))
            fi
        else
            log_warning "${service}: not running"
        fi
    done

    if [[ $errors -eq 0 ]]; then
        log_success "All services verified"
        return 0
    else
        log_error "${errors} services have issues"
        return 1
    fi
}

# =============================================================================
# Zero-Downtime Deployment
# =============================================================================

rolling_update() {
    local service_name="$1"
    local new_version="${2:-latest}"

    log_info "Rolling update for ${service_name} to version ${new_version}..."

    cd "${COMPOSE_DIR}"

    # Update service with rolling update
    docker compose -f docker-compose.services.yml up -d --no-deps --scale "${service_name}=2" "$service_name"

    # Wait for new container to be healthy
    sleep 30

    # Scale back down
    docker compose -f docker-compose.services.yml up -d --no-deps --scale "${service_name}=1" "$service_name"

    log_success "Rolling update completed for ${service_name}"
}

deploy_all_rolling() {
    log_info "Deploying all services with rolling updates..."

    for service in gateway auth weather ndvi geo alert analytics; do
        rolling_update "$service"
        sleep 10  # Stagger deployments
    done

    log_success "All services deployed"
}

# =============================================================================
# Main Entry Point
# =============================================================================

setup_services() {
    log_header "Services Setup Module"

    # Check idempotency
    if [[ -f "${SERVICES_DIR}/.initialized" ]] && [[ "${FORCE_REINIT:-false}" != "true" ]]; then
        log_info "Services already initialized. Use FORCE_REINIT=true to reinitialize."
        return 0
    fi

    setup_services_directories
    create_base_dockerfile

    for service in "${!SERVICES[@]}"; do
        create_service_dockerfile "$service"
    done

    create_docker_compose
    create_env_template

    # Mark as initialized
    date -Iseconds > "${SERVICES_DIR}/.initialized"

    log_success "Services setup completed"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-setup}" in
        setup)
            setup_services
            ;;
        build)
            build_services
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        verify)
            verify_services
            ;;
        rolling-update)
            rolling_update "${2:-gateway}" "${3:-latest}"
            ;;
        deploy-rolling)
            deploy_all_rolling
            ;;
        *)
            echo "Usage: $0 {setup|build|start|stop|verify|rolling-update|deploy-rolling}"
            exit 1
            ;;
    esac
fi

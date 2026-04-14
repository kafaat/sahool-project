#!/bin/bash
# ==============================================================================
# Part 06: Infrastructure
# Docker Compose, Monitoring, and deployment configs
# ==============================================================================

generate_infra() {
    log_info "Creating Infrastructure..."

    mkdir -p infra/{docker,monitoring/{prometheus,grafana/provisioning/{datasources,dashboards}},k8s}

    # ------------------------------------------------------------------------------
    # Docker Compose (Development)
    # ------------------------------------------------------------------------------
    write_heredoc "docker-compose.yml" << 'YAMLEOF'
version: "3.8"

services:
  # ===========================================================================
  # Databases
  # ===========================================================================
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: field_suite_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-fieldsuite}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-fieldsuite_secret}
      POSTGRES_DB: ${POSTGRES_DB:-fieldsuite_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-fieldsuite}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_net

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
      - field_suite_net

  # ===========================================================================
  # Services
  # ===========================================================================
  field-service:
    build:
      context: .
      dockerfile: services/field-service/Dockerfile
    container_name: field_suite_field
    environment:
      - ENV=development
      - DEBUG=true
      - POSTGRES_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    volumes:
      - ./services/field-service:/app
      - ./shared:/app/shared
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - field_suite_net
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  ndvi-service:
    build:
      context: .
      dockerfile: services/ndvi-service/Dockerfile
    container_name: field_suite_ndvi
    environment:
      - ENV=development
      - DEBUG=true
      - POSTGRES_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    env_file:
      - .env
    volumes:
      - ./services/ndvi-service:/app
      - ./shared:/app/shared
    ports:
      - "8002:8002"
    depends_on:
      - postgres
      - redis
    networks:
      - field_suite_net
    command: uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

  ndvi-worker:
    build:
      context: .
      dockerfile: services/ndvi-service/Dockerfile.worker
    container_name: field_suite_ndvi_worker
    environment:
      - ENV=development
      - POSTGRES_HOST=postgres
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    env_file:
      - .env
    volumes:
      - ./services/ndvi-service:/app
      - ./shared:/app/shared
    depends_on:
      - redis
      - postgres
    networks:
      - field_suite_net

  advisor-service:
    build:
      context: .
      dockerfile: services/advisor-service/Dockerfile
    container_name: field_suite_advisor
    environment:
      - ENV=development
      - DEBUG=true
      - NDVI_SERVICE_URL=http://ndvi-service:8002
      - FIELD_SERVICE_URL=http://field-service:8001
    env_file:
      - .env
    volumes:
      - ./services/advisor-service:/app
      - ./shared:/app/shared
    ports:
      - "8003:8003"
    depends_on:
      - ndvi-service
      - field-service
    networks:
      - field_suite_net
    command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

  # ===========================================================================
  # Gateway
  # ===========================================================================
  gateway:
    build:
      context: services/gateway
      dockerfile: Dockerfile
    container_name: field_suite_gateway
    ports:
      - "8000:80"
    depends_on:
      - field-service
      - ndvi-service
      - advisor-service
    networks:
      - field_suite_net

  # ===========================================================================
  # Frontend
  # ===========================================================================
  frontend:
    build:
      context: frontend
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
      - field_suite_net
    command: npm run dev -- --host

  # ===========================================================================
  # Monitoring
  # ===========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: field_suite_prometheus
    volumes:
      - ./infra/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.enable-lifecycle"
    networks:
      - field_suite_net

  grafana:
    image: grafana/grafana:10.2.2
    container_name: field_suite_grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - field_suite_net

networks:
  field_suite_net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
YAMLEOF

    # ------------------------------------------------------------------------------
    # Prometheus Config
    # ------------------------------------------------------------------------------
    write_heredoc "infra/monitoring/prometheus/prometheus.yml" << 'YAMLEOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "field-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["field-service:8001"]

  - job_name: "ndvi-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["ndvi-service:8002"]

  - job_name: "advisor-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["advisor-service:8003"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis:6379"]
YAMLEOF

    # ------------------------------------------------------------------------------
    # Grafana Datasource
    # ------------------------------------------------------------------------------
    write_heredoc "infra/monitoring/grafana/provisioning/datasources/datasources.yml" << 'YAMLEOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
YAMLEOF

    # ------------------------------------------------------------------------------
    # Grafana Dashboard
    # ------------------------------------------------------------------------------
    write_heredoc "infra/monitoring/grafana/provisioning/dashboards/dashboards.yml" << 'YAMLEOF'
apiVersion: 1

providers:
  - name: "Field Suite"
    orgId: 1
    folder: ""
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
YAMLEOF

    log_success "Infrastructure created"
}

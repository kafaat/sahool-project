#!/bin/bash
# =============================================================================
# Sahool Yemen v9.0.0 - Monitoring Module
# وحدة المراقبة والتتبع
# =============================================================================

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# =============================================================================
# Configuration
# =============================================================================

MONITORING_DIR="${DATA_DIR:-/opt/sahool}/monitoring"
GRAFANA_VERSION="${GRAFANA_VERSION:-10.2}"
PROMETHEUS_VERSION="${PROMETHEUS_VERSION:-2.48}"
LOKI_VERSION="${LOKI_VERSION:-2.9}"
TEMPO_VERSION="${TEMPO_VERSION:-2.3}"

# =============================================================================
# Setup Functions
# =============================================================================

setup_monitoring_directories() {
    log_info "Creating monitoring directories..."

    local dirs=(
        "${MONITORING_DIR}/prometheus/config"
        "${MONITORING_DIR}/prometheus/data"
        "${MONITORING_DIR}/prometheus/rules"
        "${MONITORING_DIR}/grafana/provisioning/dashboards"
        "${MONITORING_DIR}/grafana/provisioning/datasources"
        "${MONITORING_DIR}/grafana/dashboards"
        "${MONITORING_DIR}/grafana/data"
        "${MONITORING_DIR}/loki/config"
        "${MONITORING_DIR}/loki/data"
        "${MONITORING_DIR}/tempo/config"
        "${MONITORING_DIR}/tempo/data"
        "${MONITORING_DIR}/alertmanager/config"
        "${MONITORING_DIR}/alertmanager/data"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    # Set permissions for Grafana (runs as user 472)
    chown -R 472:472 "${MONITORING_DIR}/grafana"

    log_success "Monitoring directories created"
}

create_prometheus_config() {
    log_info "Creating Prometheus configuration..."

    cat > "${MONITORING_DIR}/prometheus/config/prometheus.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Prometheus Configuration v9.0.0
# =============================================================================

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'sahool-yemen'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Rule files
rule_files:
  - /etc/prometheus/rules/*.yml

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics

  # API Gateway
  - job_name: 'sahool-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: /metrics
    relabel_configs:
      - source_labels: [__address__]
        target_label: service
        replacement: gateway

  # Auth Service
  - job_name: 'sahool-auth'
    static_configs:
      - targets: ['auth:8000']
    metrics_path: /metrics

  # Weather Service
  - job_name: 'sahool-weather'
    static_configs:
      - targets: ['weather:8000']
    metrics_path: /metrics

  # NDVI Service
  - job_name: 'sahool-ndvi'
    static_configs:
      - targets: ['ndvi:8000']
    metrics_path: /metrics

  # Geo Service
  - job_name: 'sahool-geo'
    static_configs:
      - targets: ['geo:8000']
    metrics_path: /metrics

  # Alert Service
  - job_name: 'sahool-alert'
    static_configs:
      - targets: ['alert:8000']
    metrics_path: /metrics

  # Analytics Service
  - job_name: 'sahool-analytics'
    static_configs:
      - targets: ['analytics:8000']
    metrics_path: /metrics

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node Exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Docker metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
EOF

    log_success "Prometheus configuration created"
}

create_prometheus_alerts() {
    log_info "Creating Prometheus alert rules..."

    cat > "${MONITORING_DIR}/prometheus/rules/sahool-alerts.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Alert Rules v9.0.0
# =============================================================================

groups:
  - name: sahool-service-alerts
    rules:
      # Service Down
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 2 minutes."

      # High Error Rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          /
          sum(rate(http_requests_total[5m])) by (service) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.service }}."

      # High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"
          description: "95th percentile latency is {{ $value }}s on {{ $labels.service }}."

  - name: sahool-infrastructure-alerts
    rules:
      # High CPU Usage
      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}."

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
          / node_memory_MemTotal_bytes * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}% on {{ $labels.instance }}."

      # Disk Space Low
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
          / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}) * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk {{ $labels.mountpoint }} has only {{ $value }}% free space."

  - name: sahool-database-alerts
    rules:
      # PostgreSQL Down
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL database is not responding."

      # High Connection Count
      - alert: PostgreSQLHighConnections
        expr: |
          pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High PostgreSQL connection count"
          description: "Connection usage is {{ $value | humanizePercentage }}."

      # Redis Down
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis is not responding."

      # Redis Memory High
      - alert: RedisHighMemory
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is {{ $value | humanizePercentage }}."

  - name: sahool-business-alerts
    rules:
      # No NDVI Data
      - alert: NoNDVIData
        expr: |
          increase(sahool_ndvi_requests_total[1h]) == 0
        for: 2h
        labels:
          severity: warning
        annotations:
          summary: "No NDVI data received"
          description: "No NDVI requests processed in the last 2 hours."

      # Weather Data Stale
      - alert: WeatherDataStale
        expr: |
          time() - sahool_weather_last_update_timestamp > 3600
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Weather data is stale"
          description: "Weather data hasn't been updated in over an hour."
EOF

    log_success "Prometheus alert rules created"
}

create_alertmanager_config() {
    log_info "Creating Alertmanager configuration..."

    cat > "${MONITORING_DIR}/alertmanager/config/alertmanager.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Alertmanager Configuration v9.0.0
# =============================================================================

global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-receiver'
  routes:
    - match:
        severity: critical
      receiver: 'critical-receiver'
      continue: true
    - match:
        severity: warning
      receiver: 'warning-receiver'

receivers:
  - name: 'default-receiver'
    webhook_configs:
      - url: 'http://alert:8000/api/v1/alerts/webhook'
        send_resolved: true

  - name: 'critical-receiver'
    webhook_configs:
      - url: 'http://alert:8000/api/v1/alerts/webhook?priority=critical'
        send_resolved: true

  - name: 'warning-receiver'
    webhook_configs:
      - url: 'http://alert:8000/api/v1/alerts/webhook?priority=warning'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
EOF

    log_success "Alertmanager configuration created"
}

create_loki_config() {
    log_info "Creating Loki configuration..."

    cat > "${MONITORING_DIR}/loki/config/loki.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Loki Configuration v9.0.0
# =============================================================================

auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  max_entries_limit_per_query: 5000

compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/rules
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
EOF

    log_success "Loki configuration created"
}

create_tempo_config() {
    log_info "Creating Tempo configuration..."

    cat > "${MONITORING_DIR}/tempo/config/tempo.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Tempo Configuration v9.0.0
# =============================================================================

server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
        http:
    jaeger:
      protocols:
        thrift_http:
        grpc:
    zipkin:

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1_000_000
  max_block_duration: 5m

compactor:
  compaction:
    compaction_window: 1h
    max_block_bytes: 100_000_000
    block_retention: 48h
    compacted_block_retention: 1h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks
    wal:
      path: /tmp/tempo/wal
    pool:
      max_workers: 100
      queue_depth: 10000

querier:
  frontend_worker:
    frontend_address: tempo:9095

metrics_generator:
  registry:
    external_labels:
      source: tempo
      cluster: sahool-yemen
  storage:
    path: /tmp/tempo/generator/wal
  traces_storage:
    path: /tmp/tempo/generator/traces
EOF

    log_success "Tempo configuration created"
}

create_grafana_datasources() {
    log_info "Creating Grafana datasources..."

    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/datasources.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Grafana Datasources v9.0.0
# =============================================================================

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
    jsonData:
      maxLines: 1000

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: false
    jsonData:
      httpMethod: GET
      tracesToLogs:
        datasourceUid: Loki
        tags: ['service.name']
        mappedTags: [{ key: 'service.name', value: 'service' }]
        mapTagNamesEnabled: true
        spanStartTimeShift: '-1h'
        spanEndTimeShift: '1h'
        filterByTraceID: true
        filterBySpanID: false

  - name: PostgreSQL
    type: postgres
    url: postgres:5432
    database: sahool
    user: sahool_monitor
    secureJsonData:
      password: ${PG_MONITOR_PASSWORD}
    jsonData:
      sslmode: disable
      maxOpenConns: 5
      maxIdleConns: 2
    editable: false
EOF

    log_success "Grafana datasources created"
}

create_grafana_dashboards_config() {
    log_info "Creating Grafana dashboard provisioning..."

    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'Sahool Dashboards'
    orgId: 1
    folder: 'Sahool Yemen'
    folderUid: sahool
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Grafana dashboard provisioning created"
}

create_sahool_dashboard() {
    log_info "Creating Sahool overview dashboard..."

    cat > "${MONITORING_DIR}/grafana/dashboards/sahool-overview.json" << 'EOF'
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {"color": "green", "value": null},
              {"color": "red", "value": 80}
            ]
          },
          "unit": "short"
        }
      },
      "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
      "id": 1,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": ["lastNotNull"],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.0",
      "targets": [
        {
          "expr": "sum(up{job=~\"sahool-.*\"})",
          "legendFormat": "Services Up"
        }
      ],
      "title": "Services Up",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      },
      "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0},
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "area"
      },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m]))",
          "legendFormat": "RPS"
        }
      ],
      "title": "Requests/sec",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit"
        }
      },
      "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0},
      "id": 3,
      "options": {
        "colorMode": "value"
      },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
          "legendFormat": "Error Rate"
        }
      ],
      "title": "Error Rate",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "unit": "s"
        }
      },
      "gridPos": {"h": 4, "w": 4, "x": 12, "y": 0},
      "id": 4,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "P95 Latency"
        }
      ],
      "title": "P95 Latency",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "custom": {
            "lineWidth": 1
          }
        }
      },
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
      "id": 5,
      "options": {
        "legend": {"showLegend": true}
      },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m])) by (service)",
          "legendFormat": "{{service}}"
        }
      ],
      "title": "Requests by Service",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
      "id": 6,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))",
          "legendFormat": "{{service}}"
        }
      ],
      "title": "Latency by Service",
      "type": "timeseries"
    }
  ],
  "refresh": "30s",
  "schemaVersion": 38,
  "tags": ["sahool", "overview"],
  "templating": {"list": []},
  "time": {"from": "now-1h", "to": "now"},
  "title": "Sahool Yemen Overview",
  "uid": "sahool-overview",
  "version": 1
}
EOF

    log_success "Sahool overview dashboard created"
}

create_docker_compose_monitoring() {
    log_info "Creating monitoring Docker Compose configuration..."

    cat > "${MONITORING_DIR}/docker-compose.monitoring.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Monitoring Stack v9.0.0
# =============================================================================
version: '3.8'

services:
  # =========================================================================
  # Prometheus
  # =========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: sahool-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/config:/etc/prometheus:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - ./prometheus/data:/prometheus
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  # =========================================================================
  # Alertmanager
  # =========================================================================
  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: sahool-alertmanager
    restart: unless-stopped
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/config:/etc/alertmanager:ro
      - ./alertmanager/data:/alertmanager
    networks:
      - sahool-network

  # =========================================================================
  # Grafana
  # =========================================================================
  grafana:
    image: grafana/grafana:10.2.2
    container_name: sahool-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_admin_password
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s:%(http_port)s/grafana
      - GF_SERVER_SERVE_FROM_SUB_PATH=true
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./grafana/data:/var/lib/grafana
    networks:
      - sahool-network
    secrets:
      - grafana_admin_password
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # =========================================================================
  # Loki (Log Aggregation)
  # =========================================================================
  loki:
    image: grafana/loki:2.9.2
    container_name: sahool-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/loki.yml
    ports:
      - "3100:3100"
    volumes:
      - ./loki/config:/etc/loki:ro
      - ./loki/data:/loki
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3100/ready || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # =========================================================================
  # Tempo (Distributed Tracing)
  # =========================================================================
  tempo:
    image: grafana/tempo:2.3.1
    container_name: sahool-tempo
    restart: unless-stopped
    command: ["-config.file=/etc/tempo/tempo.yml"]
    ports:
      - "3200:3200"   # Tempo
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    volumes:
      - ./tempo/config:/etc/tempo:ro
      - ./tempo/data:/tmp/tempo
    networks:
      - sahool-network

  # =========================================================================
  # Promtail (Log Shipper)
  # =========================================================================
  promtail:
    image: grafana/promtail:2.9.2
    container_name: sahool-promtail
    restart: unless-stopped
    command: -config.file=/etc/promtail/promtail.yml
    volumes:
      - ./promtail/config:/etc/promtail:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    networks:
      - sahool-network

  # =========================================================================
  # Node Exporter (System Metrics)
  # =========================================================================
  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: sahool-node-exporter
    restart: unless-stopped
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
    networks:
      - sahool-network

  # =========================================================================
  # cAdvisor (Container Metrics)
  # =========================================================================
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    container_name: sahool-cadvisor
    restart: unless-stopped
    privileged: true
    devices:
      - /dev/kmsg:/dev/kmsg
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    ports:
      - "8082:8080"
    networks:
      - sahool-network

networks:
  sahool-network:
    external: true

secrets:
  grafana_admin_password:
    external: true
EOF

    log_success "Monitoring Docker Compose configuration created"
}

create_promtail_config() {
    log_info "Creating Promtail configuration..."

    mkdir -p "${MONITORING_DIR}/promtail/config"

    cat > "${MONITORING_DIR}/promtail/config/promtail.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Promtail Configuration v9.0.0
# =============================================================================

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Docker container logs
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[a-zA-Z0-9][a-zA-Z0-9_.-]+))
          source: tag
      - labels:
          stream:
          container_name:
      - output:
          source: output

  # Sahool service logs
  - job_name: sahool-services
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["com.docker.compose.project=sahool"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
EOF

    log_success "Promtail configuration created"
}

verify_monitoring() {
    log_info "Verifying monitoring configuration..."

    local errors=0

    # Check configuration files
    local configs=(
        "${MONITORING_DIR}/prometheus/config/prometheus.yml"
        "${MONITORING_DIR}/grafana/provisioning/datasources/datasources.yml"
        "${MONITORING_DIR}/loki/config/loki.yml"
        "${MONITORING_DIR}/tempo/config/tempo.yml"
        "${MONITORING_DIR}/alertmanager/config/alertmanager.yml"
    )

    for config in "${configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            log_error "Missing config: ${config}"
            ((errors++))
        fi
    done

    if [[ $errors -eq 0 ]]; then
        log_success "Monitoring configuration verified"
        return 0
    else
        log_error "Verification failed with ${errors} errors"
        return 1
    fi
}

# =============================================================================
# Main Entry Point
# =============================================================================

setup_monitoring() {
    log_header "Monitoring Setup Module"

    # Check idempotency
    if [[ -f "${MONITORING_DIR}/.initialized" ]] && [[ "${FORCE_REINIT:-false}" != "true" ]]; then
        log_info "Monitoring already initialized. Use FORCE_REINIT=true to reinitialize."
        return 0
    fi

    setup_monitoring_directories
    create_prometheus_config
    create_prometheus_alerts
    create_alertmanager_config
    create_loki_config
    create_tempo_config
    create_grafana_datasources
    create_grafana_dashboards_config
    create_sahool_dashboard
    create_promtail_config
    create_docker_compose_monitoring
    verify_monitoring

    # Mark as initialized
    date -Iseconds > "${MONITORING_DIR}/.initialized"

    log_success "Monitoring setup completed"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_monitoring "$@"
fi

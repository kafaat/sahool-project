#!/bin/bash
# =============================================================================
# Sahool Yemen v9.0.0 - Redis Module
# وحدة Redis مع TLS و ACLs
# =============================================================================

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# =============================================================================
# Configuration
# =============================================================================

REDIS_VERSION="${REDIS_VERSION:-7.2}"
REDIS_DATA_DIR="${DATA_DIR:-/opt/sahool}/redis"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_SENTINEL_PORT="${REDIS_SENTINEL_PORT:-26379}"

# =============================================================================
# Redis Setup Functions
# =============================================================================

setup_redis_directories() {
    log_info "Creating Redis directories..."

    local dirs=(
        "${REDIS_DATA_DIR}/data"
        "${REDIS_DATA_DIR}/conf"
        "${REDIS_DATA_DIR}/logs"
        "${REDIS_DATA_DIR}/certs"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    # Set permissions
    chmod 700 "${REDIS_DATA_DIR}/data"
    chmod 755 "${REDIS_DATA_DIR}/conf"
    chmod 755 "${REDIS_DATA_DIR}/logs"
    chmod 700 "${REDIS_DATA_DIR}/certs"

    log_success "Redis directories created"
}

generate_redis_acl() {
    log_info "Generating Redis ACL configuration..."

    local acl_file="${REDIS_DATA_DIR}/conf/users.acl"

    # Get passwords from Docker secrets or environment
    local admin_pass
    local app_pass
    local readonly_pass

    if [[ -f "/run/secrets/redis_password" ]]; then
        admin_pass=$(cat /run/secrets/redis_password)
    else
        admin_pass="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"
    fi

    app_pass="${REDIS_APP_PASSWORD:-$(openssl rand -base64 24)}"
    readonly_pass="${REDIS_READONLY_PASSWORD:-$(openssl rand -base64 24)}"

    cat > "$acl_file" << EOF
# Sahool Yemen Redis ACL Configuration
# Generated: $(date -Iseconds)

# Default user - disabled for security
user default off

# Admin user - full access
user admin on >${admin_pass} ~* &* +@all

# Application user - limited to application keys
user sahool_app on >${app_pass} ~sahool:* ~session:* ~cache:* ~rate:* ~events:* &sahool-events +@all -@dangerous -DEBUG -CONFIG -SHUTDOWN -BGSAVE -BGREWRITEAOF

# Read-only user for monitoring
user sahool_readonly on >${readonly_pass} ~* &* +@read +@connection +INFO +PING +CLIENT|GETNAME +CLIENT|LIST -@dangerous

# Replication user (if using sentinel)
user replicator on >${admin_pass} +PSYNC +REPLCONF +PING
EOF

    chmod 600 "$acl_file"

    # Save passwords to secrets directory
    local secrets_dir="${SECRETS_DIR:-/opt/sahool/secrets}"
    echo "$admin_pass" > "${secrets_dir}/redis_admin_password"
    echo "$app_pass" > "${secrets_dir}/redis_app_password"
    echo "$readonly_pass" > "${secrets_dir}/redis_readonly_password"
    chmod 600 "${secrets_dir}"/redis_*_password

    log_success "Redis ACL configuration generated"
}

generate_redis_config() {
    log_info "Generating Redis configuration..."

    local config_file="${REDIS_DATA_DIR}/conf/redis.conf"
    local tls_enabled="${REDIS_TLS_ENABLED:-true}"

    cat > "$config_file" << 'EOF'
# =============================================================================
# Sahool Yemen Redis Configuration v9.0.0
# =============================================================================

# Network
bind 0.0.0.0
port 6379
protected-mode yes
tcp-backlog 511
timeout 0
tcp-keepalive 300

# TLS Configuration (if enabled)
EOF

    if [[ "$tls_enabled" == "true" ]]; then
        cat >> "$config_file" << EOF
tls-port 6380
tls-cert-file ${REDIS_DATA_DIR}/certs/redis.crt
tls-key-file ${REDIS_DATA_DIR}/certs/redis.key
tls-ca-cert-file ${REDIS_DATA_DIR}/certs/ca.crt
tls-auth-clients optional
tls-protocols "TLSv1.2 TLSv1.3"
tls-ciphers DEFAULT:!MEDIUM
tls-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384
tls-prefer-server-ciphers yes
EOF
    fi

    cat >> "$config_file" << EOF

# General
daemonize no
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile ""
databases 16

# Snapshotting (RDB)
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync yes
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100

# Security
aclfile /conf/users.acl
rename-command FLUSHDB SAHOOL_FLUSHDB
rename-command FLUSHALL SAHOOL_FLUSHALL
rename-command DEBUG ""
rename-command SHUTDOWN SAHOOL_SHUTDOWN

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru
maxmemory-samples 5
active-expire-effort 1

# Lazy Freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
replica-lazy-flush yes
lazyfree-lazy-user-del yes
lazyfree-lazy-user-flush yes

# Append Only Mode (AOF)
appendonly yes
appendfilename "appendonly.aof"
appenddirname "appendonlydir"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
aof-timestamp-enabled no

# Cluster (disabled for single instance)
cluster-enabled no

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency Monitor
latency-monitor-threshold 100

# Event Notification
notify-keyspace-events "Ex"

# Advanced Config
hash-max-listpack-entries 512
hash-max-listpack-value 64
list-max-listpack-size -2
list-compress-depth 0
set-max-intset-entries 512
set-max-listpack-entries 128
set-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

    chmod 644 "$config_file"
    log_success "Redis configuration generated"
}

generate_redis_tls_certs() {
    log_info "Generating Redis TLS certificates..."

    local certs_dir="${REDIS_DATA_DIR}/certs"
    local ca_dir="${SECRETS_DIR:-/opt/sahool/secrets}/ca"

    # Use existing CA or create new one
    if [[ ! -f "${ca_dir}/ca.key" ]]; then
        mkdir -p "$ca_dir"
        openssl genrsa -out "${ca_dir}/ca.key" 4096
        openssl req -x509 -new -nodes -sha256 -days 3650 \
            -key "${ca_dir}/ca.key" \
            -out "${ca_dir}/ca.crt" \
            -subj "/C=YE/ST=Sanaa/L=Sanaa/O=Sahool Yemen/OU=Infrastructure/CN=Sahool CA"
        chmod 600 "${ca_dir}/ca.key"
    fi

    # Generate Redis server certificate
    openssl genrsa -out "${certs_dir}/redis.key" 2048

    cat > "${certs_dir}/redis.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = YE
ST = Sanaa
L = Sanaa
O = Sahool Yemen
OU = Redis
CN = redis

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = redis
DNS.2 = localhost
DNS.3 = sahool-redis
IP.1 = 127.0.0.1
EOF

    openssl req -new -key "${certs_dir}/redis.key" \
        -out "${certs_dir}/redis.csr" \
        -config "${certs_dir}/redis.cnf"

    openssl x509 -req -days 365 \
        -in "${certs_dir}/redis.csr" \
        -CA "${ca_dir}/ca.crt" \
        -CAkey "${ca_dir}/ca.key" \
        -CAcreateserial \
        -out "${certs_dir}/redis.crt" \
        -extensions v3_req \
        -extfile "${certs_dir}/redis.cnf"

    # Copy CA cert for clients
    cp "${ca_dir}/ca.crt" "${certs_dir}/ca.crt"

    # Set permissions
    chmod 600 "${certs_dir}/redis.key"
    chmod 644 "${certs_dir}/redis.crt"
    chmod 644 "${certs_dir}/ca.crt"
    rm -f "${certs_dir}/redis.csr" "${certs_dir}/redis.cnf"

    log_success "Redis TLS certificates generated"
}

create_redis_docker_compose() {
    log_info "Creating Redis Docker Compose configuration..."

    local compose_file="${REDIS_DATA_DIR}/docker-compose.redis.yml"

    cat > "$compose_file" << 'EOF'
# Sahool Yemen Redis Stack v9.0.0
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    container_name: sahool-redis
    restart: unless-stopped
    command: redis-server /conf/redis.conf
    ports:
      - "6379:6379"
      - "6380:6380"  # TLS port
    volumes:
      - redis_data:/data
      - ./conf:/conf:ro
      - ./certs:/certs:ro
      - ./logs:/var/log/redis
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "redis-cli", "--user", "sahool_readonly", "-a", "$${REDIS_READONLY_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 768M
        reservations:
          cpus: '0.25'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    ulimits:
      nofile:
        soft: 65535
        hard: 65535

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: sahool-redis-exporter
    restart: unless-stopped
    environment:
      - REDIS_ADDR=redis://redis:6379
      - REDIS_USER=sahool_readonly
      - REDIS_PASSWORD_FILE=/run/secrets/redis_readonly_password
    ports:
      - "9121:9121"
    networks:
      - sahool-network
    depends_on:
      redis:
        condition: service_healthy
    secrets:
      - redis_readonly_password

volumes:
  redis_data:
    driver: local

networks:
  sahool-network:
    external: true

secrets:
  redis_readonly_password:
    file: ${SECRETS_DIR}/redis_readonly_password
EOF

    chmod 644 "$compose_file"
    log_success "Redis Docker Compose configuration created"
}

create_redis_sentinel_config() {
    log_info "Creating Redis Sentinel configuration (for HA)..."

    local sentinel_file="${REDIS_DATA_DIR}/conf/sentinel.conf"

    cat > "$sentinel_file" << 'EOF'
# Sahool Yemen Redis Sentinel Configuration
# For High Availability deployment

port 26379
daemonize no

# Monitor master
sentinel monitor sahool-master redis 6379 2
sentinel auth-user sahool-master admin
sentinel auth-pass sahool-master ${REDIS_ADMIN_PASSWORD}

# Timing configurations
sentinel down-after-milliseconds sahool-master 30000
sentinel parallel-syncs sahool-master 1
sentinel failover-timeout sahool-master 180000

# Notification script (optional)
# sentinel notification-script sahool-master /scripts/notify.sh

# Deny scripts
sentinel deny-scripts-reconfig yes

# ACL for sentinel
aclfile /conf/sentinel-users.acl
EOF

    chmod 644 "$sentinel_file"
    log_success "Redis Sentinel configuration created"
}

verify_redis() {
    log_info "Verifying Redis configuration..."

    local errors=0

    # Check config file exists
    if [[ ! -f "${REDIS_DATA_DIR}/conf/redis.conf" ]]; then
        log_error "Redis config file missing"
        ((errors++))
    fi

    # Check ACL file exists
    if [[ ! -f "${REDIS_DATA_DIR}/conf/users.acl" ]]; then
        log_error "Redis ACL file missing"
        ((errors++))
    fi

    # Check TLS certs if enabled
    if [[ "${REDIS_TLS_ENABLED:-true}" == "true" ]]; then
        for cert in redis.crt redis.key ca.crt; do
            if [[ ! -f "${REDIS_DATA_DIR}/certs/${cert}" ]]; then
                log_error "TLS certificate missing: ${cert}"
                ((errors++))
            fi
        done
    fi

    if [[ $errors -eq 0 ]]; then
        log_success "Redis configuration verified"
        return 0
    else
        log_error "Redis verification failed with ${errors} errors"
        return 1
    fi
}

# =============================================================================
# Main Entry Point
# =============================================================================

setup_redis() {
    log_header "Redis Setup Module"

    # Check idempotency
    if [[ -f "${REDIS_DATA_DIR}/.initialized" ]] && [[ "${FORCE_REINIT:-false}" != "true" ]]; then
        log_info "Redis already initialized. Use FORCE_REINIT=true to reinitialize."
        return 0
    fi

    setup_redis_directories
    generate_redis_acl
    generate_redis_config

    if [[ "${REDIS_TLS_ENABLED:-true}" == "true" ]]; then
        generate_redis_tls_certs
    fi

    create_redis_docker_compose
    create_redis_sentinel_config
    verify_redis

    # Mark as initialized
    date -Iseconds > "${REDIS_DATA_DIR}/.initialized"

    log_success "Redis setup completed"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_redis "$@"
fi

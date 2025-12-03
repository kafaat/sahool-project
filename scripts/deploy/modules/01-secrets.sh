#!/bin/bash
# =============================================================================
# Module 01: Secrets Management
# وحدة إدارة الأسرار
# =============================================================================
# This module handles:
# - Secure secret generation
# - Docker Secrets creation
# - TLS certificate generation
# - Secret rotation support
# =============================================================================

set -euo pipefail

SECRETS_DIR="${PROJECT_ROOT}/security/secrets"
TLS_DIR="${PROJECT_ROOT}/security/tls/certs"

secrets_module() {
    log "🔐 Setting up secrets management..."

    # Check if secrets already exist
    if secrets_exist && [[ "${FORCE_RECREATE_SECRETS:-false}" != "true" ]]; then
        info "Secrets already exist. Use FORCE_RECREATE_SECRETS=true to regenerate."
        validate_secrets
        return 0
    fi

    # Generate all secrets
    generate_secrets

    # Create Docker secrets
    create_docker_secrets

    # Generate TLS certificates
    generate_tls_certificates

    # Create environment file
    create_env_file

    success "Secrets management configured"
}

secrets_exist() {
    [[ -f "${SECRETS_DIR}/db_password" ]] && \
    [[ -f "${SECRETS_DIR}/redis_password" ]] && \
    [[ -f "${SECRETS_DIR}/jwt_secret" ]]
}

validate_secrets() {
    info "Validating existing secrets..."

    local required_secrets=(
        "db_password"
        "db_root_password"
        "redis_password"
        "jwt_secret"
        "jwt_refresh_secret"
        "api_key"
        "grafana_password"
    )

    for secret in "${required_secrets[@]}"; do
        if [[ ! -f "${SECRETS_DIR}/${secret}" ]]; then
            error "Missing secret: ${secret}"
            return 1
        fi

        # Check secret is not empty
        if [[ ! -s "${SECRETS_DIR}/${secret}" ]]; then
            error "Empty secret: ${secret}"
            return 1
        fi
    done

    success "All secrets validated"
}

generate_secrets() {
    info "Generating secure secrets..."

    mkdir -p "$SECRETS_DIR"

    # Database secrets
    openssl rand -base64 48 | tr -d '\n' > "${SECRETS_DIR}/db_password"
    openssl rand -base64 48 | tr -d '\n' > "${SECRETS_DIR}/db_root_password"
    openssl rand -base64 32 | tr -d '\n' > "${SECRETS_DIR}/db_replication_password"

    # Redis secrets
    openssl rand -base64 48 | tr -d '\n' > "${SECRETS_DIR}/redis_password"

    # JWT secrets
    openssl rand -base64 64 | tr -d '\n' > "${SECRETS_DIR}/jwt_secret"
    openssl rand -base64 64 | tr -d '\n' > "${SECRETS_DIR}/jwt_refresh_secret"

    # API keys
    openssl rand -hex 64 > "${SECRETS_DIR}/api_key"
    openssl rand -hex 32 > "${SECRETS_DIR}/api_key_hash"

    # Grafana
    openssl rand -base64 24 | tr -d '\n' | head -c 16 > "${SECRETS_DIR}/grafana_password"
    openssl rand -base64 32 | tr -d '\n' > "${SECRETS_DIR}/grafana_secret_key"

    # Encryption keys
    openssl rand -base64 32 | tr -d '\n' > "${SECRETS_DIR}/encryption_key"
    openssl rand -base64 16 | tr -d '\n' > "${SECRETS_DIR}/encryption_salt"

    # Session secret
    openssl rand -hex 32 > "${SECRETS_DIR}/session_secret"

    # Set strict permissions
    chmod 600 "${SECRETS_DIR}"/*

    info "Secrets generated"
}

create_docker_secrets() {
    info "Creating Docker secrets..."

    # Remove existing secrets
    local secrets=(
        "sahool_db_password"
        "sahool_db_root_password"
        "sahool_redis_password"
        "sahool_jwt_secret"
        "sahool_jwt_refresh_secret"
        "sahool_api_key"
        "sahool_grafana_password"
        "sahool_encryption_key"
    )

    for secret in "${secrets[@]}"; do
        docker secret rm "$secret" 2>/dev/null || true
    done

    # Create new secrets (only works in Swarm mode)
    if docker info 2>/dev/null | grep -q "Swarm: active"; then
        info "Docker Swarm detected, creating secrets..."

        docker secret create sahool_db_password "${SECRETS_DIR}/db_password"
        docker secret create sahool_db_root_password "${SECRETS_DIR}/db_root_password"
        docker secret create sahool_redis_password "${SECRETS_DIR}/redis_password"
        docker secret create sahool_jwt_secret "${SECRETS_DIR}/jwt_secret"
        docker secret create sahool_jwt_refresh_secret "${SECRETS_DIR}/jwt_refresh_secret"
        docker secret create sahool_api_key "${SECRETS_DIR}/api_key"
        docker secret create sahool_grafana_password "${SECRETS_DIR}/grafana_password"
        docker secret create sahool_encryption_key "${SECRETS_DIR}/encryption_key"
    else
        info "Docker Swarm not active. Using file-based secrets."
    fi

    info "Docker secrets configured"
}

generate_tls_certificates() {
    info "Generating TLS certificates..."

    mkdir -p "$TLS_DIR"

    # Check if certificates already exist and are valid
    if [[ -f "${TLS_DIR}/server.crt" ]] && [[ -f "${TLS_DIR}/server.key" ]]; then
        # Check if certificate is not expired (within 30 days)
        if openssl x509 -checkend 2592000 -noout -in "${TLS_DIR}/server.crt" 2>/dev/null; then
            info "Valid TLS certificates exist. Skipping generation."
            return 0
        else
            warn "TLS certificates expiring soon or invalid. Regenerating..."
        fi
    fi

    # Generate CA (Certificate Authority)
    openssl genrsa -out "${TLS_DIR}/ca.key" 4096 2>/dev/null
    openssl req -new -x509 -days 3650 -key "${TLS_DIR}/ca.key" \
        -out "${TLS_DIR}/ca.crt" \
        -subj "/C=YE/ST=Sanaa/L=Sanaa/O=Sahool Yemen/OU=IT/CN=Sahool CA" \
        2>/dev/null

    # Generate server certificate
    openssl genrsa -out "${TLS_DIR}/server.key" 4096 2>/dev/null

    # Create CSR config
    cat > "${TLS_DIR}/server.cnf" <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = YE
ST = Sanaa
L = Sanaa
O = Sahool Yemen
OU = Platform
CN = sahool.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = sahool.local
DNS.3 = *.sahool.local
DNS.4 = postgres
DNS.5 = redis
DNS.6 = backend
DNS.7 = frontend
DNS.8 = gateway
IP.1 = 127.0.0.1
IP.2 = 172.20.0.1
EOF

    # Generate CSR and sign with CA
    openssl req -new -key "${TLS_DIR}/server.key" \
        -out "${TLS_DIR}/server.csr" \
        -config "${TLS_DIR}/server.cnf" \
        2>/dev/null

    openssl x509 -req -days 365 \
        -in "${TLS_DIR}/server.csr" \
        -CA "${TLS_DIR}/ca.crt" \
        -CAkey "${TLS_DIR}/ca.key" \
        -CAcreateserial \
        -out "${TLS_DIR}/server.crt" \
        -extensions v3_req \
        -extfile "${TLS_DIR}/server.cnf" \
        2>/dev/null

    # Create combined PEM for some services
    cat "${TLS_DIR}/server.crt" "${TLS_DIR}/ca.crt" > "${TLS_DIR}/server-chain.crt"

    # Generate client certificate for mTLS
    openssl genrsa -out "${TLS_DIR}/client.key" 4096 2>/dev/null
    openssl req -new -key "${TLS_DIR}/client.key" \
        -out "${TLS_DIR}/client.csr" \
        -subj "/C=YE/ST=Sanaa/L=Sanaa/O=Sahool Yemen/OU=Client/CN=sahool-client" \
        2>/dev/null
    openssl x509 -req -days 365 \
        -in "${TLS_DIR}/client.csr" \
        -CA "${TLS_DIR}/ca.crt" \
        -CAkey "${TLS_DIR}/ca.key" \
        -CAcreateserial \
        -out "${TLS_DIR}/client.crt" \
        2>/dev/null

    # Set permissions
    chmod 600 "${TLS_DIR}"/*.key
    chmod 644 "${TLS_DIR}"/*.crt

    # Cleanup
    rm -f "${TLS_DIR}"/*.csr "${TLS_DIR}"/*.cnf "${TLS_DIR}"/*.srl

    info "TLS certificates generated"
}

create_env_file() {
    info "Creating environment file..."

    local env_file="${PROJECT_ROOT}/.env"

    # Read secrets
    local db_password=$(cat "${SECRETS_DIR}/db_password")
    local db_root_password=$(cat "${SECRETS_DIR}/db_root_password")
    local redis_password=$(cat "${SECRETS_DIR}/redis_password")
    local jwt_secret=$(cat "${SECRETS_DIR}/jwt_secret")
    local jwt_refresh_secret=$(cat "${SECRETS_DIR}/jwt_refresh_secret")
    local api_key=$(cat "${SECRETS_DIR}/api_key")
    local grafana_password=$(cat "${SECRETS_DIR}/grafana_password")
    local encryption_key=$(cat "${SECRETS_DIR}/encryption_key")

    cat > "$env_file" <<EOF
# =============================================================================
# SAHOOL Yemen Platform - Environment Configuration
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Deployment ID: ${DEPLOYMENT_ID}
# =============================================================================

# Environment
ENVIRONMENT=${ENVIRONMENT:-production}
VERSION=${VERSION}
DEBUG=false

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=sahool_production
DB_USER=sahool_app
DB_PASSWORD=${db_password}
DB_ROOT_PASSWORD=${db_root_password}
DATABASE_URL=postgresql://sahool_app:${db_password}@postgres:5432/sahool_production

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${redis_password}
REDIS_URL=redis://:${redis_password}@redis:6379/0

# JWT
JWT_SECRET_KEY=${jwt_secret}
JWT_REFRESH_SECRET_KEY=${jwt_refresh_secret}
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# API
API_KEY=${api_key}

# Encryption
ENCRYPTION_KEY=${encryption_key}

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${grafana_password}

# External APIs (configure manually)
OPENAI_API_KEY=
SENTINEL_CLIENT_ID=
SENTINEL_CLIENT_SECRET=
OPENWEATHER_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
CORS_ORIGINS=*
EOF

    chmod 600 "$env_file"

    # Create example file (safe to commit)
    create_env_example

    info "Environment file created"
}

create_env_example() {
    cat > "${PROJECT_ROOT}/.env.example" <<EOF
# =============================================================================
# SAHOOL Yemen Platform - Environment Configuration Example
# Copy to .env and fill in values
# =============================================================================

# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=sahool_production
DB_USER=sahool_app
DB_PASSWORD=<generate-secure-password>
DB_ROOT_PASSWORD=<generate-secure-password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<generate-secure-password>

# JWT
JWT_SECRET_KEY=<generate-64-byte-base64>
JWT_REFRESH_SECRET_KEY=<generate-64-byte-base64>

# API
API_KEY=<generate-hex-key>

# External APIs
OPENAI_API_KEY=sk-xxx
SENTINEL_CLIENT_ID=xxx
SENTINEL_CLIENT_SECRET=xxx
OPENWEATHER_API_KEY=xxx
EOF
}

# Run module
secrets_module

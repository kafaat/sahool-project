#!/bin/bash
# =============================================================================
# Sahool Yemen v9.0.0 - Gateway Module
# وحدة بوابة API و توازن الحمل
# =============================================================================

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# =============================================================================
# Configuration
# =============================================================================

GATEWAY_DIR="${DATA_DIR:-/opt/sahool}/gateway"
NGINX_VERSION="${NGINX_VERSION:-1.25}"
DOMAIN="${SAHOOL_DOMAIN:-sahool.local}"

# =============================================================================
# Setup Functions
# =============================================================================

setup_gateway_directories() {
    log_info "Creating gateway directories..."

    local dirs=(
        "${GATEWAY_DIR}/nginx/conf.d"
        "${GATEWAY_DIR}/nginx/ssl"
        "${GATEWAY_DIR}/nginx/logs"
        "${GATEWAY_DIR}/nginx/cache"
        "${GATEWAY_DIR}/nginx/html"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    log_success "Gateway directories created"
}

generate_ssl_certificates() {
    log_info "Generating SSL certificates..."

    local ssl_dir="${GATEWAY_DIR}/nginx/ssl"
    local ca_dir="${SECRETS_DIR:-/opt/sahool/secrets}/ca"

    # Create CA if not exists
    if [[ ! -f "${ca_dir}/ca.key" ]]; then
        mkdir -p "$ca_dir"
        openssl genrsa -out "${ca_dir}/ca.key" 4096
        openssl req -x509 -new -nodes -sha256 -days 3650 \
            -key "${ca_dir}/ca.key" \
            -out "${ca_dir}/ca.crt" \
            -subj "/C=YE/ST=Sanaa/L=Sanaa/O=Sahool Yemen/OU=Infrastructure/CN=Sahool CA"
        chmod 600 "${ca_dir}/ca.key"
    fi

    # Generate server certificate
    cat > "${ssl_dir}/server.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = YE
ST = Sanaa
L = Sanaa
O = Sahool Yemen
OU = API Gateway
CN = ${DOMAIN}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = *.${DOMAIN}
DNS.3 = localhost
DNS.4 = api.${DOMAIN}
DNS.5 = grafana.${DOMAIN}
IP.1 = 127.0.0.1
EOF

    openssl genrsa -out "${ssl_dir}/server.key" 2048
    openssl req -new -key "${ssl_dir}/server.key" \
        -out "${ssl_dir}/server.csr" \
        -config "${ssl_dir}/server.cnf"

    openssl x509 -req -days 365 \
        -in "${ssl_dir}/server.csr" \
        -CA "${ca_dir}/ca.crt" \
        -CAkey "${ca_dir}/ca.key" \
        -CAcreateserial \
        -out "${ssl_dir}/server.crt" \
        -extensions v3_req \
        -extfile "${ssl_dir}/server.cnf"

    # Create fullchain
    cat "${ssl_dir}/server.crt" "${ca_dir}/ca.crt" > "${ssl_dir}/fullchain.crt"

    # Generate DH parameters
    if [[ ! -f "${ssl_dir}/dhparam.pem" ]]; then
        log_info "Generating DH parameters (this may take a while)..."
        openssl dhparam -out "${ssl_dir}/dhparam.pem" 2048
    fi

    # Set permissions
    chmod 600 "${ssl_dir}/server.key"
    chmod 644 "${ssl_dir}/server.crt" "${ssl_dir}/fullchain.crt"

    # Cleanup
    rm -f "${ssl_dir}/server.csr" "${ssl_dir}/server.cnf"

    log_success "SSL certificates generated"
}

create_nginx_main_config() {
    log_info "Creating main Nginx configuration..."

    cat > "${GATEWAY_DIR}/nginx/nginx.conf" << 'EOF'
# =============================================================================
# Sahool Yemen Nginx Configuration v9.0.0
# =============================================================================

user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    log_format json_combined escape=json '{'
        '"time":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"request":"$request",'
        '"status":"$status",'
        '"body_bytes_sent":"$body_bytes_sent",'
        '"request_time":"$request_time",'
        '"upstream_response_time":"$upstream_response_time",'
        '"http_referrer":"$http_referer",'
        '"http_user_agent":"$http_user_agent",'
        '"request_id":"$request_id"'
    '}';

    access_log /var/log/nginx/access.log json_combined;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Buffer sizes
    client_body_buffer_size 16k;
    client_header_buffer_size 1k;
    client_max_body_size 50m;
    large_client_header_buffers 4 8k;

    # Timeouts
    client_body_timeout 60s;
    client_header_timeout 60s;
    send_timeout 60s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript
               application/xml application/rss+xml application/atom+xml image/svg+xml;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # Upstream cache
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m
                     max_size=1g inactive=60m use_temp_path=off;

    # Upstream definitions
    include /etc/nginx/conf.d/upstreams.conf;

    # Server configurations
    include /etc/nginx/conf.d/*.conf;
}
EOF

    log_success "Main Nginx configuration created"
}

create_upstream_config() {
    log_info "Creating upstream configuration..."

    cat > "${GATEWAY_DIR}/nginx/conf.d/upstreams.conf" << 'EOF'
# =============================================================================
# Sahool Yemen Upstream Configuration
# =============================================================================

# API Gateway service
upstream gateway {
    zone gateway 64k;
    server gateway:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Authentication service
upstream auth {
    zone auth 64k;
    server auth:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# Weather service
upstream weather {
    zone weather 64k;
    server weather:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# NDVI service
upstream ndvi {
    zone ndvi 64k;
    server ndvi:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# Geo service
upstream geo {
    zone geo 64k;
    server geo:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# Alert service
upstream alert {
    zone alert 64k;
    server alert:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# Analytics service
upstream analytics {
    zone analytics 64k;
    server analytics:8000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# Grafana
upstream grafana {
    zone grafana 64k;
    server grafana:3000 max_fails=3 fail_timeout=30s;
    keepalive 8;
}

# Prometheus
upstream prometheus {
    zone prometheus 64k;
    server prometheus:9090 max_fails=3 fail_timeout=30s;
    keepalive 8;
}
EOF

    log_success "Upstream configuration created"
}

create_api_server_config() {
    log_info "Creating API server configuration..."

    cat > "${GATEWAY_DIR}/nginx/conf.d/api.conf" << EOF
# =============================================================================
# Sahool Yemen API Server Configuration
# =============================================================================

# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} api.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} api.${DOMAIN};

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # Request ID for tracing
    set \$request_id \$request_id;
    if (\$http_x_request_id) {
        set \$request_id \$http_x_request_id;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 '{"status":"healthy","service":"nginx"}';
        add_header Content-Type application/json;
    }

    # Nginx status for monitoring
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # API Gateway - main API routes
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;
        limit_conn conn_limit 100;

        proxy_pass http://gateway;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Request-ID \$request_id;
        proxy_set_header Connection "";

        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 8k;

        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID" always;

        if (\$request_method = OPTIONS) {
            return 204;
        }
    }

    # Authentication endpoints - stricter rate limiting
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;

        proxy_pass http://gateway;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Request-ID \$request_id;
        proxy_set_header Connection "";
    }

    # WebSocket support for real-time alerts
    location /ws/ {
        proxy_pass http://gateway;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 3600s;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
        internal;
    }
}
EOF

    log_success "API server configuration created"
}

create_monitoring_server_config() {
    log_info "Creating monitoring server configuration..."

    cat > "${GATEWAY_DIR}/nginx/conf.d/monitoring.conf" << EOF
# =============================================================================
# Sahool Yemen Monitoring Server Configuration
# =============================================================================

# Grafana
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name grafana.${DOMAIN};

    ssl_certificate /etc/nginx/ssl/fullchain.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    location / {
        proxy_pass http://grafana;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Prometheus (internal only)
server {
    listen 9091 ssl http2;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/fullchain.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    # Restrict access
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;

    location / {
        proxy_pass http://prometheus;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

    log_success "Monitoring server configuration created"
}

create_error_pages() {
    log_info "Creating custom error pages..."

    cat > "${GATEWAY_DIR}/nginx/html/50x.html" << 'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خطأ في الخادم - سهول اليمن</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a5f2a 0%, #0d3d16 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 2rem;
        }
        h1 {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .retry-btn {
            margin-top: 2rem;
            padding: 1rem 2rem;
            background: rgba(255,255,255,0.2);
            border: 2px solid white;
            color: white;
            font-size: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .retry-btn:hover {
            background: white;
            color: #1a5f2a;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚠️</h1>
        <h2>خطأ في الخادم</h2>
        <p>نعتذر، حدث خطأ أثناء معالجة طلبك.</p>
        <p>يرجى المحاولة مرة أخرى بعد قليل.</p>
        <button class="retry-btn" onclick="location.reload()">إعادة المحاولة</button>
    </div>
</body>
</html>
EOF

    log_success "Custom error pages created"
}

create_docker_compose_gateway() {
    log_info "Creating gateway Docker Compose configuration..."

    cat > "${GATEWAY_DIR}/docker-compose.gateway.yml" << 'EOF'
# =============================================================================
# Sahool Yemen Gateway Stack v9.0.0
# =============================================================================
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    container_name: sahool-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/html:/usr/share/nginx/html:ro
      - ./nginx/logs:/var/log/nginx
      - ./nginx/cache:/var/cache/nginx
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - gateway
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 64M
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "5"

networks:
  sahool-network:
    external: true
EOF

    log_success "Gateway Docker Compose configuration created"
}

verify_gateway() {
    log_info "Verifying gateway configuration..."

    local errors=0

    # Check nginx configuration syntax
    if command -v nginx &> /dev/null; then
        if ! nginx -t -c "${GATEWAY_DIR}/nginx/nginx.conf" 2>/dev/null; then
            log_error "Nginx configuration syntax error"
            ((errors++))
        fi
    fi

    # Check required files
    local required_files=(
        "${GATEWAY_DIR}/nginx/nginx.conf"
        "${GATEWAY_DIR}/nginx/conf.d/upstreams.conf"
        "${GATEWAY_DIR}/nginx/conf.d/api.conf"
        "${GATEWAY_DIR}/nginx/ssl/server.key"
        "${GATEWAY_DIR}/nginx/ssl/server.crt"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Missing file: ${file}"
            ((errors++))
        fi
    done

    if [[ $errors -eq 0 ]]; then
        log_success "Gateway configuration verified"
        return 0
    else
        log_error "Gateway verification failed with ${errors} errors"
        return 1
    fi
}

# =============================================================================
# Main Entry Point
# =============================================================================

setup_gateway() {
    log_header "Gateway Setup Module"

    # Check idempotency
    if [[ -f "${GATEWAY_DIR}/.initialized" ]] && [[ "${FORCE_REINIT:-false}" != "true" ]]; then
        log_info "Gateway already initialized. Use FORCE_REINIT=true to reinitialize."
        return 0
    fi

    setup_gateway_directories
    generate_ssl_certificates
    create_nginx_main_config
    create_upstream_config
    create_api_server_config
    create_monitoring_server_config
    create_error_pages
    create_docker_compose_gateway
    verify_gateway

    # Mark as initialized
    date -Iseconds > "${GATEWAY_DIR}/.initialized"

    log_success "Gateway setup completed"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_gateway "$@"
fi

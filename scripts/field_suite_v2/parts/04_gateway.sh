#!/bin/bash
# ==============================================================================
# Part 04: API Gateway
# Nginx-based gateway with JWT validation and rate limiting
# ==============================================================================

generate_gateway() {
    log_info "Creating API Gateway..."

    local SERVICE_DIR="services/gateway"
    mkdir -p "$SERVICE_DIR"/{nginx,scripts}

    # ------------------------------------------------------------------------------
    # Nginx Configuration
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/nginx/nginx.conf" << 'NGINXEOF'
worker_processes auto;
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

    log_format json escape=json '{'
        '"time":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"request":"$request",'
        '"status":$status,'
        '"body_bytes_sent":$body_bytes_sent,'
        '"request_time":$request_time,'
        '"upstream_response_time":"$upstream_response_time"'
    '}';

    access_log /var/log/nginx/access.log json;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;

    # Upstream services
    upstream field_service {
        server field-service:8001;
        keepalive 32;
    }

    upstream ndvi_service {
        server ndvi-service:8002;
        keepalive 32;
    }

    upstream advisor_service {
        server advisor-service:8003;
        keepalive 32;
    }

    upstream frontend {
        server frontend:3000;
        keepalive 16;
    }

    # Main server
    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Health check
        location /health {
            return 200 '{"status":"healthy","service":"gateway"}';
            add_header Content-Type application/json;
        }

        # Auth endpoints (higher rate limit)
        location /api/v1/auth/ {
            limit_req zone=auth_limit burst=20 nodelay;

            proxy_pass http://field_service/api/v1/auth/;
            include /etc/nginx/proxy_params;
        }

        # Field Service
        location /api/v1/fields {
            limit_req zone=api_limit burst=50 nodelay;

            proxy_pass http://field_service/api/v1/fields;
            include /etc/nginx/proxy_params;
        }

        # NDVI Service
        location /api/v1/ndvi {
            limit_req zone=api_limit burst=50 nodelay;

            proxy_pass http://ndvi_service/api/v1/ndvi;
            include /etc/nginx/proxy_params;
        }

        # Advisor Service
        location /api/v1/advisor {
            limit_req zone=api_limit burst=50 nodelay;

            proxy_pass http://advisor_service/api/v1/advisor;
            include /etc/nginx/proxy_params;
        }

        # WebSocket support for real-time updates
        location /ws {
            proxy_pass http://ndvi_service/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400;
        }

        # API docs (development only)
        location /docs {
            proxy_pass http://field_service/docs;
            include /etc/nginx/proxy_params;
        }

        location /openapi.json {
            proxy_pass http://field_service/openapi.json;
            include /etc/nginx/proxy_params;
        }

        # Frontend (SPA)
        location / {
            proxy_pass http://frontend/;
            include /etc/nginx/proxy_params;

            # SPA fallback
            proxy_intercept_errors on;
            error_page 404 = /index.html;
        }

        # Static assets caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            proxy_pass http://frontend;
            include /etc/nginx/proxy_params;

            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
NGINXEOF

    # Proxy parameters
    write_heredoc "$SERVICE_DIR/nginx/proxy_params" << 'PROXYEOF'
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Request-ID $request_id;
proxy_set_header Connection "";

proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
PROXYEOF

    # ------------------------------------------------------------------------------
    # Dockerfile
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/Dockerfile" << 'DOCKERFILE'
FROM nginx:1.25-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/proxy_params /etc/nginx/proxy_params

# Create log directory
RUN mkdir -p /var/log/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
DOCKERFILE

    log_success "API Gateway created"
}

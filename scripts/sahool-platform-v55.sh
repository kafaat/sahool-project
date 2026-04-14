#!/bin/bash
# ============================================================
# SAHOOL Platform Complete Setup Script v5.5
# Full-Stack Smart Agriculture Platform
# 9 Microservices + Mobile App + Infrastructure
# ============================================================

set -e

# ==================== CONFIGURATION ====================
VERSION="5.5.0"
SCRIPT_NAME="sahool-platform-v55"
PROJECT_DIR="${1:-sahool-platform}"

# ==================== COLORS ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# ==================== LOGGING ====================
log() { echo -e "${GREEN}[${SCRIPT_NAME}]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

print_header() {
    echo -e ""
    echo -e "${CYAN}${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║     SAHOOL Platform v${VERSION} - Complete Setup        ║${NC}"
    echo -e "${CYAN}${BOLD}║     Smart Agricultural Platform                       ║${NC}"
    echo -e "${CYAN}${BOLD}║     9 Microservices + Mobile App                      ║${NC}"
    echo -e "${CYAN}${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
    echo -e ""
}

print_step() {
    echo -e ""
    echo -e "${MAGENTA}${BOLD}══════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}${BOLD}  Step $1: $2${NC}"
    echo -e "${MAGENTA}${BOLD}══════════════════════════════════════════════════════${NC}"
}

# ==================== REQUIREMENTS CHECK ====================
check_requirements() {
    print_step "0" "Checking Requirements"

    local missing=()

    for cmd in node npm docker git python3; do
        if command -v $cmd &> /dev/null; then
            info "$cmd: $(command -v $cmd)"
        else
            missing+=("$cmd")
        fi
    done

    # Check docker compose
    if docker compose version &>/dev/null 2>&1; then
        info "docker compose v2: available"
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose &>/dev/null; then
        info "docker-compose v1: available"
        DOCKER_COMPOSE="docker-compose"
    else
        missing+=("docker-compose")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing requirements: ${missing[*]}"
    fi

    success "All requirements satisfied"
}

# ==================== DIRECTORY STRUCTURE ====================
create_directory_structure() {
    print_step "1" "Creating Directory Structure"

    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    # Backend services directories
    mkdir -p api-gateway
    mkdir -p db/migrations db/seeds
    mkdir -p geo-service/src/{routes,services,models}
    mkdir -p weather-service/src/{routes,services,models}
    mkdir -p imagery-service/src/{routes,services,models}
    mkdir -p agent-service/src/{routes,services,models}
    mkdir -p alerts-service/src/{routes,services,models}
    mkdir -p analytics-service/src/{routes,services,models}
    mkdir -p ndvi-engine-service/app/{api,core,services}
    mkdir -p zones-engine/app/{api,core,services}
    mkdir -p advisor-engine/app/{api,core,services}

    # Mobile app directories
    mkdir -p sahool-mobile-v4/{app/tabs,components/ui,components/cards,hooks,lib/api,store,types,assets}

    # Config directories
    mkdir -p .github/workflows
    mkdir -p scripts

    success "Directory structure created"
}

# ==================== DOCKER COMPOSE ====================
create_docker_compose() {
    print_step "2" "Creating Docker Compose Configuration"

    cat > docker-compose.yml << 'DOCKEREOF'
version: '3.9'

services:
  # ==================== INFRASTRUCTURE ====================
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: sahool-postgres
    environment:
      POSTGRES_USER: sahool
      POSTGRES_PASSWORD: sahool_secure_2024
      POSTGRES_DB: sahool_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sahool -d sahool_platform"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sahool-network

  redis:
    image: redis:7-alpine
    container_name: sahool-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sahool-network

  # ==================== API GATEWAY ====================
  kong:
    image: kong:3.4-alpine
    container_name: sahool-kong
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/kong.yml
      KONG_PROXY_LISTEN: 0.0.0.0:9000
      KONG_ADMIN_LISTEN: 0.0.0.0:9001
      KONG_LOG_LEVEL: info
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./api-gateway/kong.yml:/kong/kong.yml:ro
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== NODE.JS MICROSERVICES ====================
  geo-service:
    build:
      context: ./geo-service
      dockerfile: Dockerfile
    container_name: sahool-geo
    environment:
      PORT: 3001
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  weather-service:
    build:
      context: ./weather-service
      dockerfile: Dockerfile
    container_name: sahool-weather
    environment:
      PORT: 3002
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      OPENWEATHER_API_KEY: ${OPENWEATHER_API_KEY:-demo}
      NODE_ENV: production
    ports:
      - "3002:3002"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  imagery-service:
    build:
      context: ./imagery-service
      dockerfile: Dockerfile
    container_name: sahool-imagery
    environment:
      PORT: 3003
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    ports:
      - "3003:3003"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  agent-service:
    build:
      context: ./agent-service
      dockerfile: Dockerfile
    container_name: sahool-agent
    environment:
      PORT: 3004
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY:-demo}
      NODE_ENV: production
    ports:
      - "3004:3004"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  alerts-service:
    build:
      context: ./alerts-service
      dockerfile: Dockerfile
    container_name: sahool-alerts
    environment:
      PORT: 3005
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    ports:
      - "3005:3005"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  analytics-service:
    build:
      context: ./analytics-service
      dockerfile: Dockerfile
    container_name: sahool-analytics
    environment:
      PORT: 3006
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    ports:
      - "3006:3006"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3006/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  # ==================== PYTHON MICROSERVICES ====================
  ndvi-engine:
    build:
      context: ./ndvi-engine-service
      dockerfile: Dockerfile
    container_name: sahool-ndvi-engine
    environment:
      PORT: 8001
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
    ports:
      - "8001:8001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  zones-engine:
    build:
      context: ./zones-engine
      dockerfile: Dockerfile
    container_name: sahool-zones-engine
    environment:
      PORT: 8002
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
    ports:
      - "8002:8002"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

  advisor-engine:
    build:
      context: ./advisor-engine
      dockerfile: Dockerfile
    container_name: sahool-advisor-engine
    environment:
      PORT: 8003
      DATABASE_URL: postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY:-demo}
    ports:
      - "8003:8003"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-network
    depends_on:
      postgres:
        condition: service_healthy

networks:
  sahool-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
DOCKEREOF
    success "Created: docker-compose.yml"
}

# ==================== API GATEWAY (KONG) ====================
create_api_gateway() {
    print_step "3" "Creating API Gateway Configuration"

    cat > api-gateway/kong.yml << 'KONGEOF'
_format_version: "3.0"
_transform: true

services:
  # Geo Service
  - name: geo-service
    url: http://geo-service:3001
    routes:
      - name: geo-route
        paths:
          - /api/geo
        strip_path: true

  # Weather Service
  - name: weather-service
    url: http://weather-service:3002
    routes:
      - name: weather-route
        paths:
          - /api/weather
        strip_path: true

  # Imagery Service
  - name: imagery-service
    url: http://imagery-service:3003
    routes:
      - name: imagery-route
        paths:
          - /api/imagery
        strip_path: true

  # Agent Service (AI)
  - name: agent-service
    url: http://agent-service:3004
    routes:
      - name: agent-route
        paths:
          - /api/agent
        strip_path: true

  # Alerts Service
  - name: alerts-service
    url: http://alerts-service:3005
    routes:
      - name: alerts-route
        paths:
          - /api/alerts
        strip_path: true

  # Analytics Service
  - name: analytics-service
    url: http://analytics-service:3006
    routes:
      - name: analytics-route
        paths:
          - /api/analytics
        strip_path: true

  # NDVI Engine (Python)
  - name: ndvi-engine
    url: http://ndvi-engine:8001
    routes:
      - name: ndvi-route
        paths:
          - /api/ndvi
        strip_path: true

  # Zones Engine (Python)
  - name: zones-engine
    url: http://zones-engine:8002
    routes:
      - name: zones-route
        paths:
          - /api/zones
        strip_path: true

  # Advisor Engine (Python)
  - name: advisor-engine
    url: http://advisor-engine:8003
    routes:
      - name: advisor-route
        paths:
          - /api/advisor
        strip_path: true

plugins:
  - name: cors
    config:
      origins:
        - "*"
      methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Authorization
        - Content-Type
        - X-Tenant-ID
        - X-Request-ID
      exposed_headers:
        - X-Request-ID
      credentials: true
      max_age: 3600

  - name: rate-limiting
    config:
      minute: 100
      hour: 5000
      policy: local

  - name: request-transformer
    config:
      add:
        headers:
          - "X-Gateway-Version:v5.5"
KONGEOF
    success "Created: api-gateway/kong.yml"
}

# ==================== DATABASE SCHEMA ====================
create_database_schema() {
    print_step "4" "Creating Database Schema"

    cat > db/init.sql << 'DBEOF'
-- SAHOOL Platform Database Schema v5.5
-- PostgreSQL with PostGIS Extension

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== TENANTS ====================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== USERS ====================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'farmer',
    avatar_url TEXT,
    preferences JSONB DEFAULT '{"language": "ar", "units": "metric", "notifications": true}',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== FIELDS ====================
CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    crop_type VARCHAR(100),
    acreage DECIMAL(10, 2),
    health_score INTEGER DEFAULT 0,
    boundary GEOMETRY(POLYGON, 4326),
    center GEOMETRY(POINT, 4326),
    soil_type VARCHAR(100),
    irrigation_type VARCHAR(100),
    planting_date DATE,
    expected_harvest DATE,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== NDVI DATA ====================
CREATE TABLE IF NOT EXISTS ndvi_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    capture_date DATE NOT NULL,
    ndvi_value DECIMAL(4, 3),
    min_value DECIMAL(4, 3),
    max_value DECIMAL(4, 3),
    mean_value DECIMAL(4, 3),
    satellite VARCHAR(50),
    cloud_coverage DECIMAL(5, 2),
    raster_path TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== MANAGEMENT ZONES ====================
CREATE TABLE IF NOT EXISTS management_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    zone_number INTEGER NOT NULL,
    name VARCHAR(100),
    zone_type VARCHAR(50),
    boundary GEOMETRY(POLYGON, 4326),
    area_hectares DECIMAL(10, 2),
    avg_ndvi DECIMAL(4, 3),
    productivity_class VARCHAR(20),
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== EQUIPMENT ====================
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'idle',
    fuel_level DECIMAL(5, 2) DEFAULT 100,
    location GEOMETRY(POINT, 4326),
    last_maintenance DATE,
    next_maintenance DATE,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== ALERTS ====================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== WEATHER DATA ====================
CREATE TABLE IF NOT EXISTS weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    location GEOMETRY(POINT, 4326),
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(5, 2),
    wind_direction INTEGER,
    precipitation DECIMAL(5, 2),
    pressure DECIMAL(6, 2),
    condition VARCHAR(100),
    forecast JSONB DEFAULT '[]',
    alerts JSONB DEFAULT '[]',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== AI CONVERSATIONS ====================
CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    image_url TEXT,
    tokens_used INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== ANALYTICS ====================
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    properties JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    device_info JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== INDEXES ====================
CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fields_boundary ON fields USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_ndvi_field_date ON ndvi_data(field_id, capture_date DESC);
CREATE INDEX IF NOT EXISTS idx_zones_field ON management_zones(field_id);
CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(tenant_id, is_read) WHERE is_read = false;
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_equipment_tenant ON equipment(tenant_id);
CREATE INDEX IF NOT EXISTS idx_analytics_tenant_date ON analytics_events(tenant_id, created_at DESC);

-- ==================== SEED DATA ====================
INSERT INTO tenants (id, name, slug) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Demo Farm', 'demo-tenant')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO users (id, tenant_id, email, password_hash, name, role) VALUES
    ('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'farmer@demo.sahool.agri', '$2b$10$demo_hash_placeholder', 'Ahmed Al-Farmer', 'farmer')
ON CONFLICT (email) DO NOTHING;

INSERT INTO fields (id, tenant_id, user_id, name, crop_type, acreage, health_score, center) VALUES
    ('550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'North Wheat Field', 'wheat', 150.5, 85, ST_SetSRID(ST_MakePoint(46.6753, 24.7136), 4326)),
    ('550e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'South Date Palm Grove', 'dates', 75.0, 92, ST_SetSRID(ST_MakePoint(46.6853, 24.7036), 4326)),
    ('550e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'East Alfalfa Field', 'alfalfa', 200.0, 78, ST_SetSRID(ST_MakePoint(46.6953, 24.7236), 4326))
ON CONFLICT DO NOTHING;

INSERT INTO equipment (id, tenant_id, name, type, status, fuel_level) VALUES
    ('550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440001', 'John Deere 8R 410', 'tractor', 'active', 85),
    ('550e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440001', 'Valley 8000 Series', 'pivot', 'active', 100),
    ('550e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440001', 'DJI Agras T40', 'drone', 'idle', 60)
ON CONFLICT DO NOTHING;

INSERT INTO alerts (tenant_id, field_id, type, severity, title, message) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'weather', 'medium', 'Heat Wave Alert', 'High temperatures expected over the next 3 days. Consider increasing irrigation.'),
    ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440005', 'pest', 'high', 'Aphid Detection', 'Early signs of aphid infestation detected in sector 3. Immediate action recommended.')
ON CONFLICT DO NOTHING;
DBEOF
    success "Created: db/init.sql"
}

# ==================== NODE.JS MICROSERVICE TEMPLATE ====================
create_node_service() {
    local service_name=$1
    local port=$2
    local description=$3

    info "Creating $service_name..."

    # Package.json
    cat > "$service_name/package.json" << EOF
{
  "name": "@sahool/${service_name}",
  "version": "5.5.0",
  "description": "${description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "compression": "^1.7.4",
    "pg": "^8.11.3",
    "redis": "^4.6.12",
    "uuid": "^9.0.1",
    "dotenv": "^16.4.1",
    "winston": "^3.11.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.3",
    "jest": "^29.7.0"
  }
}
EOF

    # Dockerfile
    cat > "$service_name/Dockerfile" << 'EOF'
FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache curl

COPY package*.json ./
RUN npm ci --only=production

COPY src ./src

EXPOSE 3001

CMD ["node", "src/index.js"]
EOF

    # Main application
    cat > "$service_name/src/index.js" << EOF
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || ${port};

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: '${service_name}',
    version: '5.5.0',
    timestamp: new Date().toISOString()
  });
});

// API Info
app.get('/', (req, res) => {
  res.json({
    service: '${service_name}',
    version: '5.5.0',
    description: '${description}',
    endpoints: [
      'GET /health',
      'GET /'
    ]
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(\`${service_name} running on port \${PORT}\`);
});
EOF

    success "Created: $service_name"
}

# ==================== PYTHON MICROSERVICE TEMPLATE ====================
create_python_service() {
    local service_name=$1
    local port=$2
    local description=$3

    info "Creating $service_name..."

    # Requirements
    cat > "$service_name/requirements.txt" << 'EOF'
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
httpx==0.27.0
asyncpg==0.29.0
redis==5.0.1
numpy==1.26.4
EOF

    # Dockerfile
    cat > "$service_name/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE ${port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:${port}/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${port}"]
EOF

    # __init__.py files
    touch "$service_name/app/__init__.py"
    touch "$service_name/app/api/__init__.py"
    touch "$service_name/app/core/__init__.py"
    touch "$service_name/app/services/__init__.py"

    # Config
    cat > "$service_name/app/core/config.py" << EOF
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """${description} Configuration"""
    DATABASE_URL: str = "postgres://sahool:sahool_secure_2024@postgres:5432/sahool_platform"
    REDIS_URL: str = "redis://redis:6379"
    PORT: int = ${port}
    ENV: str = "production"

    model_config = {
        "env_prefix": "${service_name^^}_",
        "case_sensitive": False
    }


settings = Settings()
EOF

    # Main application
    cat > "$service_name/app/main.py" << EOF
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="${description}",
    version="5.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "${service_name}",
        "version": "5.5.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    return {
        "service": "${service_name}",
        "version": "5.5.0",
        "description": "${description}",
        "endpoints": [
            "GET /health",
            "GET /docs"
        ]
    }
EOF

    success "Created: $service_name"
}

# ==================== CREATE ALL MICROSERVICES ====================
create_microservices() {
    print_step "5" "Creating Microservices"

    # Node.js Services (6)
    create_node_service "geo-service" "3001" "Geographic data and field management service"
    create_node_service "weather-service" "3002" "Weather data and forecasting service"
    create_node_service "imagery-service" "3003" "Satellite imagery processing service"
    create_node_service "agent-service" "3004" "AI Assistant and chat service"
    create_node_service "alerts-service" "3005" "Alerts and notifications service"
    create_node_service "analytics-service" "3006" "Analytics and reporting service"

    # Python Services (3)
    create_python_service "ndvi-engine-service" "8001" "NDVI Calculation Engine"
    create_python_service "zones-engine" "8002" "Management Zones Engine"
    create_python_service "advisor-engine" "8003" "AI Advisory Engine"

    success "All microservices created"
}

# ==================== MOBILE APP ====================
create_mobile_app() {
    print_step "6" "Creating Mobile App"

    local mobile_dir="sahool-mobile-v4"

    # Package.json
    cat > "$mobile_dir/package.json" << 'MOBILEEOF'
{
  "name": "sahool-mobile-v4",
  "version": "5.5.0",
  "description": "SAHOOL Smart Agriculture Mobile App",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "lint": "eslint .",
    "test": "jest"
  },
  "dependencies": {
    "expo": "~51.0.0",
    "expo-router": "~3.5.0",
    "expo-status-bar": "~1.12.1",
    "expo-location": "~17.0.1",
    "expo-notifications": "~0.28.0",
    "expo-image-picker": "~15.0.4",
    "expo-secure-store": "~13.0.1",
    "expo-linear-gradient": "~12.7.2",
    "expo-splash-screen": "~0.27.4",
    "react": "18.2.0",
    "react-native": "0.74.1",
    "react-native-reanimated": "~3.10.0",
    "react-native-gesture-handler": "~2.16.0",
    "react-native-safe-area-context": "4.10.1",
    "react-native-screens": "3.31.1",
    "react-native-maps": "1.14.0",
    "react-native-svg": "~15.2.0",
    "nativewind": "^4.0.1",
    "@tanstack/react-query": "^5.25.0",
    "zustand": "^4.5.2",
    "axios": "^1.6.8",
    "@react-native-async-storage/async-storage": "^1.23.1",
    "lucide-react-native": "^0.363.0",
    "@shopify/flash-list": "^1.6.4"
  },
  "devDependencies": {
    "@babel/core": "^7.24.0",
    "@types/react": "~18.2.79",
    "tailwindcss": "^3.4.3",
    "typescript": "~5.3.3"
  }
}
MOBILEEOF

    # Types
    cat > "$mobile_dir/types/index.ts" << 'TYPESEOF'
export interface Field {
  id: string;
  name: string;
  tenantId: string;
  cropType: string;
  acreage: number;
  healthScore: number;
  boundaryPolygon: { latitude: number; longitude: number }[];
  center: { latitude: number; longitude: number };
  equipment?: Equipment[];
  ndviHistory?: NDVIEntry[];
  createdAt: string;
  updatedAt: string;
}

export interface Equipment {
  id: string;
  name: string;
  type: string;
  status: "active" | "idle" | "maintenance";
  fuel: number;
  location: { latitude: number; longitude: number };
  lastUpdate: string;
}

export interface NDVIEntry {
  date: string;
  value: number;
  satellite: string;
  cloudCoverage: number;
}

export interface WeatherData {
  current: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    condition: string;
  };
  forecast: { date: string; temperature: { min: number; max: number }; precipitation: number; condition: string }[];
  alerts: WeatherAlert[];
}

export interface WeatherAlert {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "extreme";
  title: string;
  description: string;
  startTime: string;
  endTime: string;
}

export interface Alert {
  id: string;
  type: "pest" | "disease" | "weather" | "equipment";
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  fieldId?: string;
  equipmentId?: string;
  isRead: boolean;
  createdAt: string;
}

export interface Zone {
  id: string;
  fieldId: string;
  zoneNumber: number;
  name: string;
  boundary: { latitude: number; longitude: number }[];
  areaHectares: number;
  avgNdvi: number;
  productivityClass: "high" | "medium" | "low";
  recommendations: string[];
}

export interface User {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  role: "farmer" | "manager" | "admin";
  avatar?: string;
  preferences: {
    language: "ar" | "en";
    units: "metric" | "imperial";
    notifications: boolean;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  meta?: { total: number; page: number; limit: number };
}
TYPESEOF

    # Store
    cat > "$mobile_dir/store/appStore.ts" << 'STOREEOF'
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Field, User, Alert } from "@/types";

export interface AppState {
  tenantId: string;
  setTenantId: (id: string) => void;
  user: User | null;
  setUser: (user: User | null) => void;
  selectedField: Field | null;
  setSelectedField: (field: Field | null) => void;
  fields: Field[];
  setFields: (fields: Field[]) => void;
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  markAlertAsRead: (alertId: string) => void;
  reset: () => void;
}

const initialState = {
  tenantId: process.env.EXPO_PUBLIC_TENANT_ID || "demo-tenant",
  user: null,
  selectedField: null,
  fields: [],
  alerts: [],
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,
      setTenantId: (id) => set({ tenantId: id }),
      setUser: (user) => set({ user }),
      setSelectedField: (field) => set({ selectedField: field }),
      setFields: (fields) => set({ fields }),
      setAlerts: (alerts) => set({ alerts }),
      markAlertAsRead: (alertId) => set((state) => ({
        alerts: state.alerts.map((alert) =>
          alert.id === alertId ? { ...alert, isRead: true } : alert
        ),
      })),
      reset: () => {
        set(initialState);
        AsyncStorage.removeItem("app-storage");
      },
    }),
    {
      name: "app-storage",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
STOREEOF

    # API Client
    cat > "$mobile_dir/lib/api/client.ts" << 'APIEOF'
import axios, { AxiosInstance, AxiosResponse } from "axios";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import { ApiResponse, Field, WeatherData, NDVIEntry, Alert, Zone } from "@/types";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:9000/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });
    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(async (config) => {
      const token = await SecureStore.getItemAsync("sahool_token");
      if (token) config.headers.Authorization = `Bearer ${token}`;
      config.headers["X-Tenant-ID"] = process.env.EXPO_PUBLIC_TENANT_ID;
      config.headers["X-Platform"] = Platform.OS;
      return config;
    });
  }

  // Geo Service
  async getFields(tenantId: string): Promise<AxiosResponse<ApiResponse<Field[]>>> {
    return this.client.get(`/geo/fields?tenantId=${tenantId}`);
  }

  async getFieldDetails(fieldId: string): Promise<AxiosResponse<ApiResponse<Field>>> {
    return this.client.get(`/geo/fields/${fieldId}`);
  }

  // Weather Service
  async getWeatherData(lat: number, lon: number): Promise<AxiosResponse<ApiResponse<WeatherData>>> {
    return this.client.get(`/weather/forecast?lat=${lat}&lon=${lon}`);
  }

  // NDVI Service
  async getNDVITimeline(fieldId: string): Promise<AxiosResponse<ApiResponse<NDVIEntry[]>>> {
    return this.client.get(`/ndvi/timeline/${fieldId}`);
  }

  // Zones Service
  async getManagementZones(fieldId: string): Promise<AxiosResponse<ApiResponse<Zone[]>>> {
    return this.client.get(`/zones/field/${fieldId}`);
  }

  // Alerts Service
  async getActiveAlerts(tenantId: string): Promise<AxiosResponse<ApiResponse<Alert[]>>> {
    return this.client.get(`/alerts/active?tenantId=${tenantId}`);
  }

  // AI Agent
  async chatWithAI(message: string, context: any): Promise<AxiosResponse<ApiResponse<{ reply: string }>>> {
    return this.client.post("/agent/chat", { message, context });
  }
}

export const api = new ApiClient();
APIEOF

    # Hooks
    cat > "$mobile_dir/hooks/useSahoolData.ts" << 'HOOKEOF'
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/store/appStore";
import { Field, WeatherData, NDVIEntry, Alert, Zone } from "@/types";

export function useFields() {
  const { tenantId } = useAppStore();
  return useQuery<Field[]>({
    queryKey: ["fields", tenantId],
    queryFn: async () => {
      const response = await api.getFields(tenantId);
      return response.data.data;
    },
    enabled: !!tenantId,
    staleTime: 1000 * 60 * 10,
  });
}

export function useWeather(lat: number, lon: number) {
  return useQuery<WeatherData>({
    queryKey: ["weather", lat, lon],
    queryFn: async () => {
      const response = await api.getWeatherData(lat, lon);
      return response.data.data;
    },
    refetchInterval: 1000 * 60 * 15,
  });
}

export function useNDVI(fieldId: string) {
  return useQuery<NDVIEntry[]>({
    queryKey: ["ndvi", fieldId],
    queryFn: async () => {
      const response = await api.getNDVITimeline(fieldId);
      return response.data.data;
    },
    enabled: !!fieldId,
  });
}

export function useZones(fieldId: string) {
  return useQuery<Zone[]>({
    queryKey: ["zones", fieldId],
    queryFn: async () => {
      const response = await api.getManagementZones(fieldId);
      return response.data.data;
    },
    enabled: !!fieldId,
  });
}

export function useAlerts() {
  const { tenantId } = useAppStore();
  return useQuery<Alert[]>({
    queryKey: ["alerts", tenantId],
    queryFn: async () => {
      const response = await api.getActiveAlerts(tenantId);
      return response.data.data;
    },
    enabled: !!tenantId,
    refetchInterval: 1000 * 60 * 5,
  });
}

export function useAIChat() {
  return useMutation({
    mutationFn: async ({ message, context }: { message: string; context: any }) => {
      const response = await api.chatWithAI(message, context);
      return response.data.data;
    },
  });
}
HOOKEOF

    # Root Layout
    cat > "$mobile_dir/app/_layout.tsx" << 'LAYOUTEOF'
import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as SplashScreen from "expo-splash-screen";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <StatusBar style="light" backgroundColor="#0D1F17" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "#0D1F17" },
          }}
        >
          <Stack.Screen name="(tabs)" />
        </Stack>
      </GestureHandlerRootView>
    </QueryClientProvider>
  );
}
LAYOUTEOF

    # Tab Layout
    cat > "$mobile_dir/app/tabs/_layout.tsx" << 'TABLAYOUTEOF'
import { Tabs } from "expo-router";
import { Platform } from "react-native";
import { Home, Map, Layers, Bell, Brain, User } from "lucide-react-native";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#1B4D3E",
          borderTopWidth: 0,
          height: Platform.OS === "ios" ? 85 : 65,
          paddingBottom: Platform.OS === "ios" ? 25 : 10,
        },
        tabBarActiveTintColor: "#F4D03F",
        tabBarInactiveTintColor: "rgba(255, 255, 255, 0.5)",
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="fields"
        options={{
          title: "Fields",
          tabBarIcon: ({ color, size }) => <Map size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="ndvi"
        options={{
          title: "NDVI",
          tabBarIcon: ({ color, size }) => <Layers size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="zones"
        options={{
          title: "Zones",
          tabBarIcon: ({ color, size }) => <Layers size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="alerts"
        options={{
          title: "Alerts",
          tabBarIcon: ({ color, size }) => <Bell size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="assistant"
        options={{
          title: "AI",
          tabBarIcon: ({ color, size }) => <Brain size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
TABLAYOUTEOF

    # Home Screen
    cat > "$mobile_dir/app/tabs/index.tsx" << 'HOMEEOF'
import React from "react";
import { View, Text, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import { useFields, useAlerts } from "@/hooks/useSahoolData";

export default function HomeScreen() {
  const { data: fields, isLoading } = useFields();
  const { data: alerts } = useAlerts();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#F4D03F" />
        <Text style={styles.loadingText}>Loading your farm...</Text>
      </View>
    );
  }

  const urgentAlerts = alerts?.filter(a => a.severity === "high" || a.severity === "critical") || [];
  const avgHealth = fields?.length
    ? Math.round(fields.reduce((sum, f) => sum + f.healthScore, 0) / fields.length)
    : 0;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>SAHOOL Dashboard</Text>
        <Text style={styles.subtitle}>{fields?.length || 0} active fields</Text>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{avgHealth}%</Text>
          <Text style={styles.statLabel}>Avg Health</Text>
        </View>
        <View style={[styles.statCard, styles.alertCard]}>
          <Text style={styles.statValue}>{urgentAlerts.length}</Text>
          <Text style={styles.statLabel}>Urgent Alerts</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Fields</Text>
        {fields?.map((field) => (
          <View key={field.id} style={styles.fieldCard}>
            <Text style={styles.fieldName}>{field.name}</Text>
            <Text style={styles.fieldInfo}>{field.cropType} • {field.acreage} ha</Text>
            <Text style={styles.fieldHealth}>Health: {field.healthScore}%</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0D1F17" },
  loading: { flex: 1, backgroundColor: "#0D1F17", alignItems: "center", justifyContent: "center" },
  loadingText: { color: "#F4D03F", marginTop: 16, fontSize: 16 },
  header: { padding: 20, paddingTop: 60 },
  greeting: { fontSize: 28, fontWeight: "900", color: "#FFFFFF" },
  subtitle: { fontSize: 16, color: "#F4D03F", marginTop: 4 },
  statsGrid: { flexDirection: "row", padding: 16, gap: 12 },
  statCard: { flex: 1, backgroundColor: "#1B4D3E", padding: 20, borderRadius: 16 },
  alertCard: { backgroundColor: "#E74C3C" },
  statValue: { fontSize: 32, fontWeight: "900", color: "#FFFFFF" },
  statLabel: { fontSize: 14, color: "rgba(255,255,255,0.7)", marginTop: 4 },
  section: { padding: 16 },
  sectionTitle: { fontSize: 20, fontWeight: "700", color: "#FFFFFF", marginBottom: 16 },
  fieldCard: { backgroundColor: "#1B4D3E", padding: 16, borderRadius: 12, marginBottom: 12 },
  fieldName: { fontSize: 18, fontWeight: "700", color: "#FFFFFF" },
  fieldInfo: { fontSize: 14, color: "rgba(255,255,255,0.6)", marginTop: 4 },
  fieldHealth: { fontSize: 14, color: "#F4D03F", marginTop: 8 },
});
HOMEEOF

    # Create placeholder screens
    for screen in fields ndvi zones alerts assistant; do
        cat > "$mobile_dir/app/tabs/${screen}.tsx" << EOF
import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function ${screen^}Screen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>${screen^}</Text>
      <Text style={styles.subtitle}>Coming in v5.5...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0D1F17", alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
  subtitle: { fontSize: 16, color: "#F4D03F", marginTop: 8 },
});
EOF
    done

    success "Created: Mobile App"
}

# ==================== UTILITY FILES ====================
create_utility_files() {
    print_step "7" "Creating Utility Files"

    # Makefile
    cat > Makefile << 'MAKEEOF'
.PHONY: all build up down logs clean test

all: build up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v --rmi local

test:
	./verify.sh

mobile:
	cd sahool-mobile-v4 && npm install && npm start
MAKEEOF

    # Verify script
    cat > verify.sh << 'VERIFYEOF'
#!/bin/bash
echo "🔍 Verifying SAHOOL Platform v5.5..."

services=(
    "http://localhost:9000:Kong Gateway"
    "http://localhost:3001/health:Geo Service"
    "http://localhost:3002/health:Weather Service"
    "http://localhost:3003/health:Imagery Service"
    "http://localhost:3004/health:Agent Service"
    "http://localhost:3005/health:Alerts Service"
    "http://localhost:3006/health:Analytics Service"
    "http://localhost:8001/health:NDVI Engine"
    "http://localhost:8002/health:Zones Engine"
    "http://localhost:8003/health:Advisor Engine"
)

failed=0
for service in "${services[@]}"; do
    url="${service%%:*}"
    name="${service##*:}"
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|301"; then
        echo "✅ $name"
    else
        echo "❌ $name"
        ((failed++))
    fi
done

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 All services healthy!"
else
    echo ""
    echo "⚠️  $failed service(s) failed"
fi
VERIFYEOF
    chmod +x verify.sh

    # README
    cat > README.md << 'READMEEOF'
# SAHOOL Platform v5.5

Smart Agricultural Platform - Complete Stack

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kong API Gateway (:9000)                 │
├─────────────────────────────────────────────────────────────┤
│  Node.js Services          │  Python Services              │
│  ├── geo-service    :3001  │  ├── ndvi-engine    :8001     │
│  ├── weather-service:3002  │  ├── zones-engine   :8002     │
│  ├── imagery-service:3003  │  └── advisor-engine :8003     │
│  ├── agent-service  :3004  │                               │
│  ├── alerts-service :3005  │                               │
│  └── analytics      :3006  │                               │
├─────────────────────────────────────────────────────────────┤
│        PostgreSQL + PostGIS (:5432) │ Redis (:6379)        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Start all services
docker compose up -d --build

# Verify
./verify.sh

# Run mobile app
cd sahool-mobile-v4
npm install
npm start
```

## Endpoints

| Service | Port | Path |
|---------|------|------|
| API Gateway | 9000 | / |
| Kong Admin | 9001 | / |
| Geo Service | 3001 | /api/geo |
| Weather | 3002 | /api/weather |
| Imagery | 3003 | /api/imagery |
| AI Agent | 3004 | /api/agent |
| Alerts | 3005 | /api/alerts |
| Analytics | 3006 | /api/analytics |
| NDVI Engine | 8001 | /api/ndvi |
| Zones Engine | 8002 | /api/zones |
| Advisor | 8003 | /api/advisor |

## License

MIT - SAHOOL Team
READMEEOF

    # .env.example
    cat > .env.example << 'ENVEOF'
# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key
OPENAI_API_KEY=your_openai_api_key

# Database
POSTGRES_USER=sahool
POSTGRES_PASSWORD=sahool_secure_2024
POSTGRES_DB=sahool_platform

# Redis
REDIS_URL=redis://redis:6379
ENVEOF

    # .gitignore
    cat > .gitignore << 'IGNOREEOF'
node_modules/
.env
*.log
.DS_Store
dist/
build/
__pycache__/
*.pyc
.venv/
IGNOREEOF

    success "Created: Utility files"
}

# ==================== GIT INIT ====================
init_git_repo() {
    print_step "8" "Initializing Git Repository"

    if [ ! -d ".git" ]; then
        git init
        git branch -M main
        git add .
        git commit -m "Initial commit: SAHOOL Platform v5.5"
        success "Git repository initialized"
    else
        warn "Git repository already exists"
    fi
}

# ==================== MAIN ====================
main() {
    print_header

    check_requirements
    create_directory_structure
    create_docker_compose
    create_api_gateway
    create_database_schema
    create_microservices
    create_mobile_app
    create_utility_files
    init_git_repo

    echo -e ""
    echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║              Setup Complete! 🎉                       ║${NC}"
    echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
    echo -e ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. ${WHITE}cd ${PROJECT_DIR}${NC}"
    echo -e "  2. ${WHITE}docker compose up -d --build${NC}"
    echo -e "  3. ${WHITE}./verify.sh${NC}"
    echo -e "  4. ${WHITE}cd sahool-mobile-v4 && npm install && npm start${NC}"
    echo -e ""
    echo -e "${MAGENTA}Services:${NC}"
    echo -e "  API Gateway: ${BLUE}http://localhost:9000${NC}"
    echo -e "  Kong Admin:  ${BLUE}http://localhost:9001${NC}"
    echo -e "  PostgreSQL:  ${BLUE}localhost:5432${NC}"
    echo -e "  Redis:       ${BLUE}localhost:6379${NC}"
    echo -e ""
}

# Execute
main "$@"

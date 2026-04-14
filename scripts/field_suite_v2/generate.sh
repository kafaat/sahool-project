#!/bin/bash
# ==============================================================================
# Field Suite Platform v2.0 - Production-Ready Generator
# SAHOOL-aligned Enterprise Architecture
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Colors and Variables
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

PROJECT_NAME="${1:-field_suite_platform}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------------------------------------------------------
# Helper Functions (FIXED - no smart quotes)
# ------------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# FIXED: Proper write_file function
write_file() {
    local file_path="$1"
    local content="$2"

    mkdir -p "$(dirname "$file_path")"
    printf '%s\n' "$content" > "$file_path"
}

# Write file from heredoc (safer for complex content)
write_heredoc() {
    local file_path="$1"
    mkdir -p "$(dirname "$file_path")"
    cat > "$file_path"
}

print_banner() {
    echo -e "${GREEN}"
    echo "============================================================"
    echo "     Field Suite Platform v2.0 - Production Generator"
    echo "     SAHOOL-aligned Enterprise Architecture"
    echo "============================================================"
    echo -e "${NC}"
}

print_structure() {
    echo -e "${CYAN}"
    echo "Target Architecture:"
    echo ""
    echo "$PROJECT_NAME/"
    echo "|-- services/"
    echo "|   |-- field-service/      # Field Management"
    echo "|   |-- ndvi-service/       # NDVI Processing + Workers"
    echo "|   |-- advisor-service/    # Smart Recommendations"
    echo "|   |-- gateway/            # API Gateway (Kong/Nginx)"
    echo "|"
    echo "|-- shared/"
    echo "|   |-- schemas/            # Shared Pydantic models"
    echo "|   |-- utils/              # Common utilities"
    echo "|"
    echo "|-- infra/"
    echo "|   |-- docker/             # Docker configs"
    echo "|   |-- k8s/                # Kubernetes manifests"
    echo "|   |-- monitoring/         # Prometheus + Grafana"
    echo "|"
    echo "|-- frontend/               # React + TypeScript"
    echo "|-- governance/             # SAHOOL policies"
    echo "|-- .github/                # CI/CD workflows"
    echo -e "${NC}"
}

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
main() {
    print_banner

    log_info "Creating project: $PROJECT_NAME"
    print_structure

    # Create base directory
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"

    # Source all parts
    log_info "Loading modules..."

    source "$SCRIPT_DIR/parts/00_shared.sh"
    source "$SCRIPT_DIR/parts/01_field_service.sh"
    source "$SCRIPT_DIR/parts/02_ndvi_service.sh"
    source "$SCRIPT_DIR/parts/03_advisor_service.sh"
    source "$SCRIPT_DIR/parts/04_gateway.sh"
    source "$SCRIPT_DIR/parts/05_frontend.sh"
    source "$SCRIPT_DIR/parts/06_infra.sh"
    source "$SCRIPT_DIR/parts/07_governance.sh"

    # Execute generators
    log_info "Generating shared modules..."
    generate_shared

    log_info "Generating Field Service..."
    generate_field_service

    log_info "Generating NDVI Service..."
    generate_ndvi_service

    log_info "Generating Advisor Service..."
    generate_advisor_service

    log_info "Generating API Gateway..."
    generate_gateway

    log_info "Generating Frontend..."
    generate_frontend

    log_info "Generating Infrastructure..."
    generate_infra

    log_info "Generating Governance..."
    generate_governance

    # Final setup
    log_info "Finalizing..."

    # Create root files
    create_root_files

    log_success "Project generated successfully!"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  cd $PROJECT_NAME"
    echo "  cp .env.example .env"
    echo "  docker-compose up -d"
    echo ""
    echo -e "${CYAN}Services:${NC}"
    echo "  Field Service:   http://localhost:8001"
    echo "  NDVI Service:    http://localhost:8002"
    echo "  Advisor Service: http://localhost:8003"
    echo "  Gateway:         http://localhost:8000"
    echo "  Frontend:        http://localhost:3000"
    echo "  Grafana:         http://localhost:3001"
    echo ""
}

create_root_files() {
    # .env.example
    write_heredoc ".env.example" << 'ENVEOF'
# ==============================================================================
# Field Suite Platform - Environment Configuration
# ==============================================================================

# General
ENV=development
DEBUG=true
SECRET_KEY=change-this-in-production-use-openssl-rand-hex-32

# Database
POSTGRES_USER=fieldsuite
POSTGRES_PASSWORD=fieldsuite_secret
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=fieldsuite_db

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Services
FIELD_SERVICE_URL=http://field-service:8001
NDVI_SERVICE_URL=http://ndvi-service:8002
ADVISOR_SERVICE_URL=http://advisor-service:8003

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# External APIs (optional)
SENTINEL_CLIENT_ID=
SENTINEL_CLIENT_SECRET=
OPENWEATHER_API_KEY=
ENVEOF

    # .gitignore
    write_heredoc ".gitignore" << 'GITEOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
*.so
.eggs/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
dist/
build/
.next/

# Environment
.env
.env.local
.env.*.local
*.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# Docker
docker-compose.override.yml

# Logs
*.log
logs/

# Uploads
uploads/
tmp/
GITEOF

    # Makefile
    write_heredoc "Makefile" << 'MAKEEOF'
.PHONY: help dev prod build test clean

help:
	@echo "Field Suite Platform - Commands"
	@echo "================================"
	@echo "  make dev      - Start development environment"
	@echo "  make prod     - Start production environment"
	@echo "  make build    - Build all services"
	@echo "  make test     - Run all tests"
	@echo "  make clean    - Clean up"

dev:
	docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  Gateway:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Grafana:  http://localhost:3001"

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

build:
	docker-compose build --no-cache

test:
	docker-compose exec field-service pytest -v
	docker-compose exec ndvi-service pytest -v
	docker-compose exec advisor-service pytest -v

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

logs:
	docker-compose logs -f

shell-%:
	docker-compose exec $* bash
MAKEEOF

    # README
    write_heredoc "README.md" << 'READMEEOF'
# Field Suite Platform

Enterprise Agricultural Field Management System - SAHOOL Aligned

## Architecture

```
services/
  field-service/     - Field CRUD + GIS
  ndvi-service/      - NDVI Processing + Celery Workers
  advisor-service/   - Smart Recommendations Engine
  gateway/           - API Gateway + Auth
```

## Quick Start

```bash
cp .env.example .env
make dev
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8000 | API Gateway + JWT Auth |
| Field | 8001 | Field Management |
| NDVI | 8002 | Vegetation Analysis |
| Advisor | 8003 | Recommendations |
| Frontend | 3000 | React UI |
| Grafana | 3001 | Monitoring |

## API Documentation

- Gateway: http://localhost:8000/docs
- Field: http://localhost:8001/docs
- NDVI: http://localhost:8002/docs
- Advisor: http://localhost:8003/docs
READMEEOF
}

# Run main
main "$@"

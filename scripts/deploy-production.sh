#!/bin/bash
# =============================================================================
# SAHOOL Platform v6.8.4 - Production Deployment Script
# منصة سهول - سكربت النشر للإنتاج
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"

# Version
VERSION="6.8.4"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

header() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo -e "${NC}"
}

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  deploy       Deploy or update the platform"
    echo "  rollback     Rollback to previous version"
    echo "  status       Show deployment status"
    echo "  logs         Show service logs"
    echo "  health       Run health checks"
    echo "  scale        Scale a service"
    echo ""
    echo "Options:"
    echo "  --no-backup  Skip backup before deployment"
    echo "  --force      Force deployment without confirmations"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 rollback"
    echo "  $0 status"
    echo "  $0 scale ndvi-engine 3"
    exit 1
}

# =============================================================================
# Pre-deployment Checks
# =============================================================================

pre_deploy_checks() {
    header "Pre-deployment Checks"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    log "Docker: $(docker --version)"

    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        error "Docker Compose is not installed"
    fi
    log "Docker Compose: $(${COMPOSE_CMD} version)"

    # Check compose file
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        error "Compose file not found: ${COMPOSE_FILE}"
    fi
    log "Compose file: ${COMPOSE_FILE}"

    # Check .env file
    if [[ ! -f ".env" ]]; then
        error ".env file not found. Copy .env.example and configure it."
    fi

    # Validate required environment variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET_KEY"
        "REDIS_PASSWORD"
    )

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=CHANGE_ME" .env; then
            error "Environment variable ${var} is not set or has default value"
        fi
    done

    log "Environment variables: OK"

    # Check disk space
    local available=$(df -BG "${PROJECT_DIR}" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ ${available} -lt 10 ]]; then
        warn "Low disk space: ${available}GB available (minimum 10GB recommended)"
    else
        log "Disk space: ${available}GB available"
    fi

    # Validate Docker Compose config
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" config -q
    log "Compose configuration: Valid"

    echo ""
}

# =============================================================================
# Backup
# =============================================================================

create_backup() {
    if [[ "${BACKUP_BEFORE_DEPLOY}" == "true" ]]; then
        header "Creating Pre-deployment Backup"

        if [[ -x "./scripts/backup.sh" ]]; then
            ./scripts/backup.sh
        else
            warn "Backup script not found or not executable"
        fi
    else
        log "Skipping backup (--no-backup specified)"
    fi
}

# =============================================================================
# Deploy
# =============================================================================

deploy() {
    header "SAHOOL Platform Deployment v${VERSION}"

    pre_deploy_checks
    create_backup

    header "Pulling Latest Images"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" pull

    header "Starting Services"

    # Start infrastructure first
    log "Starting infrastructure services..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d postgres redis

    # Wait for database
    log "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=0
    while ! docker exec sahool-postgres pg_isready -U sahool_admin -d sahool 2>/dev/null; do
        attempt=$((attempt + 1))
        if [[ ${attempt} -ge ${max_attempts} ]]; then
            error "PostgreSQL did not become ready in time"
        fi
        sleep 2
    done
    log "PostgreSQL is ready"

    # Run migrations
    header "Running Database Migrations"
    if [[ -d "./db" ]]; then
        for sql_file in ./db/*.sql; do
            if [[ -f "${sql_file}" ]]; then
                log "Applying: $(basename ${sql_file})"
                docker exec -i sahool-postgres psql -U sahool_admin -d sahool < "${sql_file}" || true
            fi
        done
    fi

    # Start all services
    header "Starting Application Services"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d

    # Wait for services
    log "Waiting for services to start..."
    sleep 10

    # Health check
    header "Running Health Checks"
    health_check

    echo -e "${GREEN}"
    echo "============================================================"
    echo "  Deployment completed successfully!"
    echo "  Version: ${VERSION}"
    echo "  Time: $(date)"
    echo "============================================================"
    echo -e "${NC}"
}

# =============================================================================
# Rollback
# =============================================================================

rollback() {
    header "SAHOOL Platform Rollback"

    # List available backups
    log "Available backups:"
    ls -la ./backups/*.tar.gz 2>/dev/null || warn "No backups found"

    echo ""
    read -p "Enter backup path to restore (or 'cancel'): " BACKUP_PATH

    if [[ "${BACKUP_PATH}" == "cancel" ]]; then
        log "Rollback cancelled"
        exit 0
    fi

    if [[ ! -f "${BACKUP_PATH}" ]] && [[ ! -d "${BACKUP_PATH}" ]]; then
        error "Backup not found: ${BACKUP_PATH}"
    fi

    # Stop services
    header "Stopping Services"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down

    # Restore
    header "Restoring from Backup"
    ./scripts/restore.sh "${BACKUP_PATH}" --no-confirm

    # Restart services
    header "Restarting Services"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d

    log "Rollback completed"
}

# =============================================================================
# Status
# =============================================================================

status() {
    header "Deployment Status"

    log "Container Status:"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps

    echo ""
    log "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    echo ""
    log "Recent Logs (last 5 lines per service):"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --tail=5
}

# =============================================================================
# Health Check
# =============================================================================

health_check() {
    local services=(
        "http://localhost:9000/health|API Gateway"
        "http://localhost:8009/health|Auth Service"
        "http://localhost:8003/health|Weather Service"
    )

    local all_healthy=true

    for service in "${services[@]}"; do
        IFS='|' read -r url name <<< "${service}"

        if curl -sf "${url}" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} ${name}: healthy"
        else
            echo -e "  ${RED}✗${NC} ${name}: unhealthy"
            all_healthy=false
        fi
    done

    echo ""

    if [[ "${all_healthy}" == "true" ]]; then
        log "All services are healthy"
    else
        warn "Some services are unhealthy"
        return 1
    fi
}

# =============================================================================
# Scale
# =============================================================================

scale_service() {
    local service="$1"
    local count="$2"

    if [[ -z "${service}" ]] || [[ -z "${count}" ]]; then
        error "Usage: $0 scale <service> <count>"
    fi

    header "Scaling ${service} to ${count} instances"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d --scale "${service}=${count}"

    log "Scaling completed"
}

# =============================================================================
# Logs
# =============================================================================

show_logs() {
    local service="${1:-}"

    if [[ -n "${service}" ]]; then
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs -f "${service}"
    else
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs -f
    fi
}

# =============================================================================
# Main
# =============================================================================

cd "${PROJECT_DIR}"

# Parse global options
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            BACKUP_BEFORE_DEPLOY=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        deploy|rollback|status|health|logs|scale)
            COMMAND="$1"
            shift
            break
            ;;
        -h|--help)
            usage
            ;;
        *)
            break
            ;;
    esac
done

case "${COMMAND}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    health)
        health_check
        ;;
    logs)
        show_logs "$@"
        ;;
    scale)
        scale_service "$@"
        ;;
    *)
        usage
        ;;
esac

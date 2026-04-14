#!/bin/bash
# =============================================================================
# SAHOOL Yemen Platform - Enterprise Deployment System v10.0.0
# نظام نشر منصة سهول اليمن - إصدار المؤسسات
# =============================================================================
#
# This is the main orchestrator for the modular deployment system.
# يقوم هذا السكريبت بتنسيق وحدات النشر المختلفة
#
# Modules:
#   00-init.sh       - Environment validation and structure creation
#   01-secrets.sh    - Secure secrets management (Docker Secrets)
#   02-database.sh   - PostgreSQL with hardening and migrations
#   03-redis.sh      - Redis with TLS and ACLs
#   04-services.sh   - Microservices deployment
#   05-monitoring.sh - Observability stack (Grafana, Loki, Tempo)
#   06-gateway.sh    - API Gateway and load balancing
#
# Usage:
#   ./deploy.sh [environment] [action]
#   ./deploy.sh production deploy
#   ./deploy.sh production rollback
#   ./deploy.sh staging validate
#
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_DIR="${SCRIPT_DIR}/modules"
TEMPLATES_DIR="${SCRIPT_DIR}/templates"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

VERSION="10.0.0"
DEPLOYMENT_ID="$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 4)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# Logging Functions
# =============================================================================
log() { echo -e "${GREEN}[SAHOOL v${VERSION}]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
step() { echo -e "${MAGENTA}[STEP]${NC} $1"; }

# =============================================================================
# Pre-flight Checks
# =============================================================================
preflight_check() {
    log "🔍 Running pre-flight checks..."

    local errors=0

    # Check required tools
    local required_tools=("docker" "openssl" "jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            error "Required tool not found: $tool"
            ((errors++))
        fi
    done

    # Check Docker Compose V2
    if ! docker compose version &>/dev/null; then
        error "Docker Compose V2 not found"
        ((errors++))
    fi

    # Check Docker daemon
    if ! docker info &>/dev/null; then
        error "Docker daemon not running"
        ((errors++))
    fi

    # Check disk space (minimum 25GB)
    local available_gb=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( available_gb < 25 )); then
        error "Insufficient disk space: ${available_gb}GB (minimum 25GB required)"
        ((errors++))
    fi

    # Check memory (minimum 8GB)
    local available_mem=$(free -g 2>/dev/null | awk '/Mem:/ {print $2}' || echo "16")
    if (( available_mem < 8 )); then
        warn "Low memory: ${available_mem}GB (8GB recommended)"
    fi

    # Check modules exist
    for module in 00-init 01-secrets 02-database 03-redis 04-services 05-monitoring 06-gateway; do
        if [[ ! -f "${MODULES_DIR}/${module}.sh" ]]; then
            error "Module not found: ${module}.sh"
            ((errors++))
        fi
    done

    if (( errors > 0 )); then
        error "Pre-flight check failed with $errors error(s)"
        exit 1
    fi

    success "Pre-flight checks passed"
}

# =============================================================================
# Deployment State Management
# =============================================================================
STATE_FILE="${PROJECT_ROOT}/.deployment_state"

save_state() {
    local module=$1
    local status=$2
    echo "${module}:${status}:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATE_FILE"
}

get_last_successful_module() {
    if [[ -f "$STATE_FILE" ]]; then
        grep ":success:" "$STATE_FILE" | tail -1 | cut -d: -f1
    fi
}

clear_state() {
    rm -f "$STATE_FILE"
}

# =============================================================================
# Backup Management
# =============================================================================
create_pre_deploy_backup() {
    log "📦 Creating pre-deployment backup..."

    local backup_dir="${PROJECT_ROOT}/backups/pre_deploy_${DEPLOYMENT_ID}"
    mkdir -p "$backup_dir"

    # Backup current state
    if [[ -f "${PROJECT_ROOT}/docker-compose.yml" ]]; then
        cp "${PROJECT_ROOT}/docker-compose.yml" "$backup_dir/"
    fi

    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        cp "${PROJECT_ROOT}/.env" "$backup_dir/"
    fi

    # Backup database if running
    if docker ps --format '{{.Names}}' | grep -q "sahool.*postgres"; then
        info "Backing up database..."
        docker exec sahool-postgres pg_dumpall -U postgres 2>/dev/null | \
            gzip > "$backup_dir/database_backup.sql.gz" || true
    fi

    # Save deployment metadata
    cat > "$backup_dir/metadata.json" <<EOF
{
    "deployment_id": "${DEPLOYMENT_ID}",
    "version": "${VERSION}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "${ENVIRONMENT:-production}",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
}
EOF

    success "Backup created: $backup_dir"
    echo "$backup_dir"
}

# =============================================================================
# Rollback Function
# =============================================================================
rollback() {
    local backup_dir=$1

    if [[ -z "$backup_dir" ]] || [[ ! -d "$backup_dir" ]]; then
        error "Invalid backup directory: $backup_dir"
        exit 1
    fi

    log "🔄 Rolling back to: $backup_dir"

    # Stop current services
    docker compose -f "${PROJECT_ROOT}/docker-compose.yml" down 2>/dev/null || true

    # Restore files
    if [[ -f "$backup_dir/docker-compose.yml" ]]; then
        cp "$backup_dir/docker-compose.yml" "${PROJECT_ROOT}/"
    fi

    if [[ -f "$backup_dir/.env" ]]; then
        cp "$backup_dir/.env" "${PROJECT_ROOT}/"
    fi

    # Restore database if backup exists
    if [[ -f "$backup_dir/database_backup.sql.gz" ]]; then
        warn "Database rollback requires manual intervention"
        info "Backup file: $backup_dir/database_backup.sql.gz"
    fi

    # Restart services
    docker compose -f "${PROJECT_ROOT}/docker-compose.yml" up -d

    success "Rollback completed"
}

# =============================================================================
# Module Execution
# =============================================================================
run_module() {
    local module=$1
    local module_path="${MODULES_DIR}/${module}.sh"

    if [[ ! -f "$module_path" ]]; then
        error "Module not found: $module_path"
        return 1
    fi

    step "Running module: $module"

    # Source and execute module
    # shellcheck source=/dev/null
    if source "$module_path"; then
        save_state "$module" "success"
        success "Module completed: $module"
        return 0
    else
        save_state "$module" "failed"
        error "Module failed: $module"
        return 1
    fi
}

# =============================================================================
# Validation Function
# =============================================================================
validate_deployment() {
    log "✅ Validating deployment..."

    local errors=0

    # Check all services are running
    local services=("postgres" "redis" "backend" "frontend" "gateway")
    for service in "${services[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "sahool.*${service}"; then
            warn "Service not running: $service"
            ((errors++))
        fi
    done

    # Health checks
    local endpoints=(
        "http://localhost:8080/health"
        "http://localhost:8000/health"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -sf "$endpoint" > /dev/null 2>&1; then
            info "Health check passed: $endpoint"
        else
            warn "Health check failed: $endpoint"
            ((errors++))
        fi
    done

    if (( errors > 0 )); then
        warn "Validation completed with $errors warning(s)"
        return 1
    fi

    success "Deployment validation passed"
    return 0
}

# =============================================================================
# Main Deployment Flow
# =============================================================================
deploy() {
    local environment=${1:-production}

    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║        SAHOOL Yemen Platform - Enterprise Deployment v${VERSION}       ║"
    echo "║              نظام نشر منصة سهول اليمن الاحترافي                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log "Starting deployment for environment: $environment"
    log "Deployment ID: $DEPLOYMENT_ID"

    export ENVIRONMENT="$environment"
    export PROJECT_ROOT
    export DEPLOYMENT_ID
    export VERSION

    # Pre-flight checks
    preflight_check

    # Create backup
    local backup_dir
    backup_dir=$(create_pre_deploy_backup)

    # Clear previous state
    clear_state

    # Run modules in order
    local modules=("00-init" "01-secrets" "02-database" "03-redis" "04-services" "05-monitoring" "06-gateway")

    for module in "${modules[@]}"; do
        if ! run_module "$module"; then
            error "Deployment failed at module: $module"
            warn "Run './deploy.sh rollback $backup_dir' to restore"
            exit 1
        fi
    done

    # Validate deployment
    sleep 10  # Wait for services to start
    if ! validate_deployment; then
        warn "Deployment completed with warnings"
    fi

    # Final summary
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Deployment Completed Successfully!              ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"

    echo -e "\n${CYAN}Deployment Summary:${NC}"
    echo -e "  Environment:   ${environment}"
    echo -e "  Deployment ID: ${DEPLOYMENT_ID}"
    echo -e "  Backup:        ${backup_dir}"

    echo -e "\n${CYAN}Access Points:${NC}"
    echo -e "  Gateway:    http://localhost:8080"
    echo -e "  Backend:    http://localhost:8000"
    echo -e "  Frontend:   http://localhost:3000"
    echo -e "  Grafana:    http://localhost:3003"
    echo -e "  Prometheus: http://localhost:9091"

    echo -e "\n${CYAN}Management Commands:${NC}"
    echo -e "  Status:   ./deploy.sh status"
    echo -e "  Logs:     ./deploy.sh logs [service]"
    echo -e "  Rollback: ./deploy.sh rollback ${backup_dir}"
}

# =============================================================================
# CLI Handler
# =============================================================================
show_help() {
    cat <<EOF
SAHOOL Yemen Platform - Enterprise Deployment System v${VERSION}

Usage: ./deploy.sh [command] [options]

Commands:
  deploy [env]        Deploy the platform (default: production)
  rollback [dir]      Rollback to a previous backup
  validate            Validate current deployment
  status              Show deployment status
  logs [service]      View service logs
  stop                Stop all services
  clean               Clean up deployment artifacts
  help                Show this help message

Environments:
  production          Production environment (default)
  staging             Staging environment
  development         Development environment

Examples:
  ./deploy.sh deploy production
  ./deploy.sh rollback backups/pre_deploy_20241203_120000_abc123
  ./deploy.sh logs backend
  ./deploy.sh status

EOF
}

status() {
    log "📊 Deployment Status"

    echo -e "\n${CYAN}Docker Containers:${NC}"
    docker ps --filter "name=sahool" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo -e "\n${CYAN}Deployment State:${NC}"
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "No deployment state found"
    fi
}

logs() {
    local service=${1:-}
    if [[ -n "$service" ]]; then
        docker compose logs -f "$service"
    else
        docker compose logs -f
    fi
}

stop() {
    log "Stopping all services..."
    docker compose down
    success "All services stopped"
}

clean() {
    warn "This will remove all deployment artifacts!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose down -v --remove-orphans
        rm -rf "$STATE_FILE"
        success "Cleanup completed"
    fi
}

# =============================================================================
# Main Entry Point
# =============================================================================
main() {
    cd "$PROJECT_ROOT"

    case "${1:-deploy}" in
        deploy)
            deploy "${2:-production}"
            ;;
        rollback)
            rollback "${2:-}"
            ;;
        validate)
            validate_deployment
            ;;
        status)
            status
            ;;
        logs)
            logs "${2:-}"
            ;;
        stop)
            stop
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

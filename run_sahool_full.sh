#!/bin/bash
# ===================================================================
# SAHOOL Platform v6.8.1 - Full Execution Script
# Orchestrates: Build, Deploy, Test, and Monitor
# ===================================================================
set -euo pipefail

# ===================== CONFIGURATION =====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="sahool-platform-v6-final"
PROJECT_DIR="$SCRIPT_DIR/$PROJECT_NAME"
LOG_FILE="$SCRIPT_DIR/sahool_execution_$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ===================== LOGGING =====================
log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"; exit 1; }
header() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}║ $1${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

# ===================== HELP =====================
show_help() {
    cat << EOF
SAHOOL Platform v6.8.1 - Full Execution Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  build       Build the platform from scratch
  start       Start all services (requires build first)
  stop        Stop all running services
  restart     Restart all services
  test        Run E2E tests
  logs        Show service logs
  status      Show service status
  clean       Remove all containers and volumes
  full        Build + Start + Test (complete flow)
  flutter     Setup and run Flutter app

Options:
  -h, --help     Show this help message
  -v, --verbose  Enable verbose output
  -f, --force    Force rebuild even if exists
  --no-test      Skip tests after deployment

Examples:
  $0 full              # Complete setup and test
  $0 build             # Only build
  $0 start             # Start existing build
  $0 test              # Run tests on running system
  $0 logs auth-service # Show logs for specific service

EOF
    exit 0
}

# ===================== PRE-FLIGHT CHECKS =====================
check_dependencies() {
    header "Checking Dependencies"

    local missing=()
    for cmd in docker git curl jq openssl; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    # Check Docker Compose
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        missing+=("docker-compose")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing dependencies: ${missing[*]}"
    fi

    # Check Docker is running
    if ! docker info &>/dev/null; then
        error "Docker daemon is not running"
    fi

    log "All dependencies satisfied (Compose: $COMPOSE_CMD)"
}

check_ports() {
    header "Checking Port Availability"

    local ports=(9000 8443 5432 6379)
    local conflicts=()

    for port in "${ports[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":$port " || \
           netstat -tuln 2>/dev/null | grep -q ":$port "; then
            conflicts+=("$port")
        fi
    done

    if [[ ${#conflicts[@]} -gt 0 ]]; then
        warn "Ports in use: ${conflicts[*]}"
        echo -e "${YELLOW}Stop existing services with:${NC}"
        echo "  docker compose down"
        echo "  docker compose -f docker-compose.dev.yml down"

        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "All required ports are available"
    fi
}

# ===================== BUILD =====================
do_build() {
    header "Building SAHOOL Platform v6.8.1"

    if [[ -d "$PROJECT_DIR" && "${FORCE_BUILD:-false}" != "true" ]]; then
        warn "Project directory already exists: $PROJECT_DIR"
        read -p "Rebuild? This will backup existing. (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Using existing build"
            return 0
        fi
    fi

    cd "$SCRIPT_DIR"

    if [[ ! -f "build_sahool_v6_8_1_final_corrected.sh" ]]; then
        error "Build script not found: build_sahool_v6_8_1_final_corrected.sh"
    fi

    chmod +x build_sahool_v6_8_1_final_corrected.sh
    log "Running build script..."

    ./build_sahool_v6_8_1_final_corrected.sh 2>&1 | tee -a "$LOG_FILE"

    if [[ -d "$PROJECT_DIR" ]]; then
        log "Build completed successfully"
    else
        error "Build failed - project directory not created"
    fi
}

# ===================== START SERVICES =====================
do_start() {
    header "Starting SAHOOL Services"

    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project not built. Run: $0 build"
    fi

    cd "$PROJECT_DIR"

    log "Building Docker images..."
    $COMPOSE_CMD build 2>&1 | tee -a "$LOG_FILE"

    log "Starting services..."
    $COMPOSE_CMD up -d 2>&1 | tee -a "$LOG_FILE"

    log "Waiting for services to be healthy..."
    local max_wait=120
    local waited=0

    while [[ $waited -lt $max_wait ]]; do
        if curl -s -f "http://localhost:9000/api/auth/health" &>/dev/null; then
            log "API Gateway is ready!"
            break
        fi
        echo -n "."
        sleep 2
        waited=$((waited + 2))
    done
    echo

    if [[ $waited -ge $max_wait ]]; then
        warn "Services may not be fully ready. Check logs with: $0 logs"
    fi

    do_status
}

# ===================== STOP SERVICES =====================
do_stop() {
    header "Stopping SAHOOL Services"

    if [[ ! -d "$PROJECT_DIR" ]]; then
        warn "Project directory not found"
        return 0
    fi

    cd "$PROJECT_DIR"
    $COMPOSE_CMD down 2>&1 | tee -a "$LOG_FILE"
    log "Services stopped"
}

# ===================== RESTART =====================
do_restart() {
    do_stop
    sleep 2
    do_start
}

# ===================== STATUS =====================
do_status() {
    header "Service Status"

    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project not built"
    fi

    cd "$PROJECT_DIR"

    echo -e "\n${CYAN}Container Status:${NC}"
    $COMPOSE_CMD ps

    echo -e "\n${CYAN}Health Checks:${NC}"

    local services=(
        "auth:http://localhost:9000/api/auth/health"
        "config:http://localhost:9000/api/config/health"
        "geo:http://localhost:9000/api/geo/health"
    )

    for svc in "${services[@]}"; do
        local name="${svc%%:*}"
        local url="${svc#*:}"

        if curl -s -f "$url" &>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} $name"
        else
            echo -e "  ${RED}[FAIL]${NC} $name"
        fi
    done

    # Show credentials hint
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        echo -e "\n${CYAN}Credentials:${NC}"
        echo -e "  Admin user: ${YELLOW}admin${NC}"
        echo -e "  Password: ${YELLOW}See .env file (ADMIN_SEED_PASSWORD)${NC}"
    fi
}

# ===================== LOGS =====================
do_logs() {
    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project not built"
    fi

    cd "$PROJECT_DIR"

    local service="${1:-}"

    if [[ -n "$service" ]]; then
        $COMPOSE_CMD logs -f "$service"
    else
        $COMPOSE_CMD logs -f --tail=100
    fi
}

# ===================== TEST =====================
do_test() {
    header "Running E2E Tests"

    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project not built. Run: $0 build"
    fi

    cd "$SCRIPT_DIR"

    if [[ ! -f "e2e_test_sahool_v6_8_1.sh" ]]; then
        error "Test script not found"
    fi

    chmod +x e2e_test_sahool_v6_8_1.sh

    cd "$PROJECT_DIR"
    "$SCRIPT_DIR/e2e_test_sahool_v6_8_1.sh" 2>&1 | tee -a "$LOG_FILE"
}

# ===================== CLEAN =====================
do_clean() {
    header "Cleaning Up"

    read -p "This will remove all containers and volumes. Continue? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Cancelled"
        return 0
    fi

    if [[ -d "$PROJECT_DIR" ]]; then
        cd "$PROJECT_DIR"
        $COMPOSE_CMD down -v --remove-orphans 2>&1 | tee -a "$LOG_FILE" || true
    fi

    # Remove project directory
    if [[ -d "$PROJECT_DIR" ]]; then
        read -p "Remove project directory too? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            log "Project directory removed"
        fi
    fi

    log "Cleanup complete"
}

# ===================== FLUTTER =====================
do_flutter() {
    header "Flutter App Setup"

    if [[ ! -d "$PROJECT_DIR/sahool-flutter" ]]; then
        error "Flutter directory not found. Run: $0 build"
    fi

    if ! command -v flutter &>/dev/null; then
        error "Flutter SDK not installed"
    fi

    cd "$PROJECT_DIR/sahool-flutter"

    log "Installing dependencies..."
    flutter pub get 2>&1 | tee -a "$LOG_FILE"

    log "Generating code (Isar)..."
    flutter pub run build_runner build --delete-conflicting-outputs 2>&1 | tee -a "$LOG_FILE"

    log "Flutter setup complete!"
    echo -e "\n${CYAN}To run the app:${NC}"
    echo "  cd $PROJECT_DIR/sahool-flutter"
    echo "  flutter run"
    echo -e "\n${CYAN}For web:${NC}"
    echo "  flutter run -d chrome"
    echo -e "\n${CYAN}For Android emulator:${NC}"
    echo "  flutter run -d emulator"
}

# ===================== FULL FLOW =====================
do_full() {
    header "SAHOOL Platform v6.8.1 - Full Deployment"

    local start_time=$(date +%s)

    check_dependencies
    check_ports
    do_build
    do_start

    if [[ "${NO_TEST:-false}" != "true" ]]; then
        sleep 10  # Wait for services to stabilize
        do_test
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    header "Deployment Complete!"

    echo -e "${GREEN}Duration: ${duration}s${NC}"
    echo -e "\n${CYAN}Access Points:${NC}"
    echo "  API Gateway: http://localhost:9000/api"
    echo "  Auth Health: http://localhost:9000/api/auth/health"
    echo ""

    if [[ -f "$PROJECT_DIR/.env" ]]; then
        echo -e "${CYAN}Login Credentials:${NC}"
        echo "  Username: admin"
        echo -e "  Password: ${YELLOW}See .env file (ADMIN_SEED_PASSWORD)${NC}"
    fi

    echo -e "\n${CYAN}Next Steps:${NC}"
    echo "  1. Run Flutter app: $0 flutter"
    echo "  2. View logs: $0 logs"
    echo "  3. Check status: $0 status"
    echo ""
    echo -e "Log file: ${MAGENTA}$LOG_FILE${NC}"
}

# ===================== MAIN =====================
main() {
    # Parse options
    VERBOSE=false
    FORCE_BUILD=false
    NO_TEST=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help) show_help ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -f|--force) FORCE_BUILD=true; shift ;;
            --no-test) NO_TEST=true; shift ;;
            build) do_build; exit 0 ;;
            start) check_dependencies; do_start; exit 0 ;;
            stop) check_dependencies; do_stop; exit 0 ;;
            restart) check_dependencies; do_restart; exit 0 ;;
            status) check_dependencies; do_status; exit 0 ;;
            test) check_dependencies; do_test; exit 0 ;;
            logs) check_dependencies; shift; do_logs "$@"; exit 0 ;;
            clean) check_dependencies; do_clean; exit 0 ;;
            flutter) do_flutter; exit 0 ;;
            full) do_full; exit 0 ;;
            *)
                echo "Unknown command: $1"
                show_help
                ;;
        esac
    done

    # Default: show help
    show_help
}

# Initialize log
echo "SAHOOL Platform v6.8.1 - Execution Log" > "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

main "$@"

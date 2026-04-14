#!/bin/bash
# =============================================================================
# Sahool Yemen v9.0.0 - Common Library
# المكتبة المشتركة
# =============================================================================

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Default paths
export PROJECT_DIR="${PROJECT_DIR:-/opt/sahool}"
export DATA_DIR="${DATA_DIR:-/opt/sahool/data}"
export SECRETS_DIR="${SECRETS_DIR:-/opt/sahool/secrets}"
export LOGS_DIR="${LOGS_DIR:-/opt/sahool/logs}"
export BACKUP_DIR="${BACKUP_DIR:-/opt/sahool/backups}"

# =============================================================================
# Logging Functions
# =============================================================================

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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

log_header() {
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
}

log_step() {
    echo -e "${BLUE}-->${NC} $1"
}

# =============================================================================
# Validation Functions
# =============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi

    log_success "Docker is available"
    return 0
}

check_docker_compose() {
    if ! docker compose version &> /dev/null; then
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose is not installed"
            return 1
        fi
    fi

    log_success "Docker Compose is available"
    return 0
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    local errors=0

    # Check required commands
    local required_commands=("curl" "openssl" "jq")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            ((errors++))
        fi
    done

    # Check Docker
    if ! check_docker; then
        ((errors++))
    fi

    # Check Docker Compose
    if ! check_docker_compose; then
        ((errors++))
    fi

    # Check disk space (require at least 10GB)
    local available_space
    available_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 10 ]]; then
        log_warning "Low disk space: ${available_space}GB available (recommended: 10GB+)"
    fi

    # Check memory (require at least 4GB)
    local total_mem
    total_mem=$(free -g | awk 'NR==2 {print $2}')
    if [[ $total_mem -lt 4 ]]; then
        log_warning "Low memory: ${total_mem}GB available (recommended: 4GB+)"
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Prerequisites check failed with ${errors} errors"
        return 1
    fi

    log_success "All prerequisites met"
    return 0
}

# =============================================================================
# Network Functions
# =============================================================================

ensure_docker_network() {
    local network_name="${1:-sahool-network}"

    if ! docker network inspect "$network_name" &> /dev/null; then
        log_info "Creating Docker network: ${network_name}"
        docker network create --driver bridge "$network_name"
        log_success "Network ${network_name} created"
    else
        log_info "Network ${network_name} already exists"
    fi
}

# =============================================================================
# Secret Management Functions
# =============================================================================

generate_password() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

generate_secret() {
    local length="${1:-64}"
    openssl rand -hex "$length"
}

create_docker_secret() {
    local name="$1"
    local value="$2"

    if docker secret inspect "$name" &> /dev/null 2>&1; then
        log_info "Secret ${name} already exists"
        return 0
    fi

    echo -n "$value" | docker secret create "$name" -
    log_success "Created Docker secret: ${name}"
}

read_secret() {
    local secret_name="$1"
    local secret_file="/run/secrets/${secret_name}"
    local env_file="${SECRETS_DIR}/${secret_name}"

    if [[ -f "$secret_file" ]]; then
        cat "$secret_file"
    elif [[ -f "$env_file" ]]; then
        cat "$env_file"
    else
        log_error "Secret not found: ${secret_name}"
        return 1
    fi
}

# =============================================================================
# Backup Functions
# =============================================================================

create_backup_dir() {
    local backup_path="${BACKUP_DIR}/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

backup_file() {
    local source="$1"
    local backup_dir="${2:-$(create_backup_dir)}"

    if [[ -f "$source" ]]; then
        cp -a "$source" "${backup_dir}/"
        log_info "Backed up: ${source}"
    fi
}

backup_directory() {
    local source="$1"
    local backup_dir="${2:-$(create_backup_dir)}"

    if [[ -d "$source" ]]; then
        cp -a "$source" "${backup_dir}/"
        log_info "Backed up directory: ${source}"
    fi
}

# =============================================================================
# Docker Functions
# =============================================================================

wait_for_container() {
    local container="$1"
    local timeout="${2:-120}"
    local interval="${3:-5}"

    log_info "Waiting for container ${container} to be healthy..."

    local elapsed=0
    while [[ $elapsed -lt $timeout ]]; do
        local status
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")

        case "$status" in
            "healthy")
                log_success "Container ${container} is healthy"
                return 0
                ;;
            "unhealthy")
                log_error "Container ${container} is unhealthy"
                return 1
                ;;
            "not_found")
                log_debug "Container ${container} not found yet..."
                ;;
            *)
                log_debug "Container ${container} status: ${status}"
                ;;
        esac

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    log_error "Timeout waiting for container ${container}"
    return 1
}

stop_container() {
    local container="$1"

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_info "Stopping container: ${container}"
        docker stop "$container" &> /dev/null || true
        docker rm "$container" &> /dev/null || true
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

confirm_action() {
    local message="${1:-Are you sure?}"

    if [[ "${FORCE:-false}" == "true" ]]; then
        return 0
    fi

    read -r -p "${message} [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

get_timestamp() {
    date -Iseconds
}

get_date_tag() {
    date +%Y%m%d
}

check_port_available() {
    local port="$1"

    if command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":${port} "; then
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":${port} "; then
            return 1
        fi
    fi

    return 0
}

wait_for_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-60}"

    log_info "Waiting for ${host}:${port}..."

    local elapsed=0
    while [[ $elapsed -lt $timeout ]]; do
        if nc -z "$host" "$port" &> /dev/null 2>&1; then
            log_success "${host}:${port} is available"
            return 0
        fi

        sleep 2
        elapsed=$((elapsed + 2))
    done

    log_error "Timeout waiting for ${host}:${port}"
    return 1
}

# =============================================================================
# Environment Functions
# =============================================================================

load_env_file() {
    local env_file="${1:-.env}"

    if [[ -f "$env_file" ]]; then
        log_info "Loading environment from ${env_file}"
        set -a
        # shellcheck source=/dev/null
        source "$env_file"
        set +a
    fi
}

export_env() {
    local key="$1"
    local value="$2"

    export "$key"="$value"
}

# =============================================================================
# Error Handling
# =============================================================================

trap_error() {
    local line_no="$1"
    local error_code="$2"

    log_error "Error on line ${line_no}: exit code ${error_code}"

    if [[ "${CLEANUP_ON_ERROR:-true}" == "true" ]]; then
        cleanup_on_error
    fi

    exit "$error_code"
}

cleanup_on_error() {
    log_info "Performing cleanup after error..."
    # Override in scripts as needed
}

setup_error_trap() {
    trap 'trap_error ${LINENO} $?' ERR
}

# =============================================================================
# Version Functions
# =============================================================================

get_version() {
    echo "9.0.0"
}

compare_versions() {
    local v1="$1"
    local v2="$2"

    if [[ "$v1" == "$v2" ]]; then
        echo "equal"
    elif [[ "$(printf '%s\n' "$v1" "$v2" | sort -V | head -n1)" == "$v1" ]]; then
        echo "less"
    else
        echo "greater"
    fi
}

# =============================================================================
# Yemen-Specific Functions
# =============================================================================

get_yemen_governorates() {
    # Return list of Yemen governorates in Arabic
    cat << 'EOF'
صنعاء
عدن
تعز
الحديدة
إب
حضرموت
ذمار
المكلا
عمران
صعدة
حجة
البيضاء
شبوة
لحج
مأرب
المحويت
الجوف
أبين
الضالع
ريمة
EOF
}

# =============================================================================
# Initialization
# =============================================================================

init_common() {
    # Create base directories
    mkdir -p "${PROJECT_DIR}" "${DATA_DIR}" "${SECRETS_DIR}" "${LOGS_DIR}" "${BACKUP_DIR}"

    # Set permissions
    chmod 700 "${SECRETS_DIR}"
    chmod 755 "${PROJECT_DIR}" "${DATA_DIR}" "${LOGS_DIR}" "${BACKUP_DIR}"
}

# Export all functions
export -f log_info log_success log_warning log_error log_debug log_header log_step
export -f check_root check_docker check_docker_compose check_prerequisites
export -f ensure_docker_network
export -f generate_password generate_secret create_docker_secret read_secret
export -f create_backup_dir backup_file backup_directory
export -f wait_for_container stop_container
export -f confirm_action get_timestamp get_date_tag check_port_available wait_for_port
export -f load_env_file export_env
export -f get_version compare_versions
export -f get_yemen_governorates init_common

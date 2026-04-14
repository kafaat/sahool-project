#!/bin/bash
# =============================================================================
# SAHOOL Platform v6.8.4 - Restore Script
# منصة سهول - سكربت الاستعادة
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Database settings from environment or defaults
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-sahool}"
DB_USER="${POSTGRES_USER:-sahool_admin}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"

# Container names
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-sahool-postgres}"
REDIS_CONTAINER="${REDIS_CONTAINER:-sahool-redis}"
MINIO_CONTAINER="${MINIO_CONTAINER:-sahool-minio}"

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

usage() {
    echo "Usage: $0 <backup_path>"
    echo ""
    echo "Arguments:"
    echo "  backup_path    Path to backup directory or .tar.gz file"
    echo ""
    echo "Options:"
    echo "  --postgres-only    Restore only PostgreSQL"
    echo "  --redis-only       Restore only Redis"
    echo "  --minio-only       Restore only MinIO"
    echo "  --no-confirm       Skip confirmation prompt"
    echo ""
    echo "Example:"
    echo "  $0 ./backups/sahool_backup_20241207_120000"
    echo "  $0 ./backups/sahool_backup_20241207_120000.tar.gz"
    exit 1
}

# =============================================================================
# Main Restore Function
# =============================================================================

main() {
    local BACKUP_PATH="$1"
    local RESTORE_POSTGRES=true
    local RESTORE_REDIS=true
    local RESTORE_MINIO=true
    local NO_CONFIRM=false

    # Parse arguments
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --postgres-only)
                RESTORE_REDIS=false
                RESTORE_MINIO=false
                ;;
            --redis-only)
                RESTORE_POSTGRES=false
                RESTORE_MINIO=false
                ;;
            --minio-only)
                RESTORE_POSTGRES=false
                RESTORE_REDIS=false
                ;;
            --no-confirm)
                NO_CONFIRM=true
                ;;
            *)
                warn "Unknown option: $1"
                ;;
        esac
        shift
    done

    if [[ -z "${BACKUP_PATH}" ]]; then
        usage
    fi

    echo -e "${CYAN}"
    echo "============================================================"
    echo "  SAHOOL Platform - Restore Script v6.8.4"
    echo "  منصة سهول - الاستعادة"
    echo "============================================================"
    echo -e "${NC}"

    # Extract if archive
    if [[ "${BACKUP_PATH}" == *.tar.gz ]]; then
        log "Extracting backup archive..."
        local EXTRACT_DIR=$(mktemp -d)
        tar -xzf "${BACKUP_PATH}" -C "${EXTRACT_DIR}"
        BACKUP_PATH="${EXTRACT_DIR}/$(basename ${BACKUP_PATH%.tar.gz})"
    fi

    # Validate backup
    if [[ ! -d "${BACKUP_PATH}" ]]; then
        error "Backup directory not found: ${BACKUP_PATH}"
    fi

    # Show metadata
    if [[ -f "${BACKUP_PATH}/metadata.json" ]]; then
        log "Backup metadata:"
        cat "${BACKUP_PATH}/metadata.json"
        echo ""
    fi

    # Confirmation
    if [[ "${NO_CONFIRM}" != true ]]; then
        echo -e "${YELLOW}"
        echo "WARNING: This will overwrite existing data!"
        echo -e "${NC}"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM

        if [[ "${CONFIRM}" != "yes" ]]; then
            log "Restore cancelled by user"
            exit 0
        fi
    fi

    # Restore components
    if [[ "${RESTORE_POSTGRES}" == true ]]; then
        restore_postgres "${BACKUP_PATH}"
    fi

    if [[ "${RESTORE_REDIS}" == true ]]; then
        restore_redis "${BACKUP_PATH}"
    fi

    if [[ "${RESTORE_MINIO}" == true ]]; then
        restore_minio "${BACKUP_PATH}"
    fi

    echo -e "${GREEN}"
    echo "============================================================"
    echo "  Restore completed successfully!"
    echo "============================================================"
    echo -e "${NC}"
}

# =============================================================================
# PostgreSQL Restore
# =============================================================================

restore_postgres() {
    local BACKUP_PATH="$1"

    if [[ ! -f "${BACKUP_PATH}/database.dump" ]]; then
        warn "PostgreSQL backup not found, skipping..."
        return
    fi

    log "Starting PostgreSQL restore..."

    # Check if running in Docker
    if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
        log "Restoring PostgreSQL to Docker container..."

        # Drop existing connections
        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            psql -U "${DB_USER}" -d postgres -c \
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
            2>/dev/null || true

        # Drop and recreate database
        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"

        # Restore
        cat "${BACKUP_PATH}/database.dump" | \
            docker exec -i -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            pg_restore -U "${DB_USER}" -d "${DB_NAME}" --no-owner --verbose

    else
        log "Restoring PostgreSQL directly..."

        # Drop existing connections
        PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d postgres -c \
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
            2>/dev/null || true

        # Drop and recreate database
        PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

        PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"

        # Restore
        PGPASSWORD="${DB_PASSWORD}" pg_restore \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d "${DB_NAME}" \
            --no-owner --verbose \
            "${BACKUP_PATH}/database.dump"
    fi

    log "PostgreSQL restore completed"
}

# =============================================================================
# Redis Restore
# =============================================================================

restore_redis() {
    local BACKUP_PATH="$1"

    if [[ ! -f "${BACKUP_PATH}/redis.rdb" ]]; then
        warn "Redis backup not found, skipping..."
        return
    fi

    log "Starting Redis restore..."

    if docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
        # Stop Redis
        docker exec "${REDIS_CONTAINER}" redis-cli SHUTDOWN NOSAVE 2>/dev/null || true
        sleep 2

        # Copy dump file
        docker cp "${BACKUP_PATH}/redis.rdb" "${REDIS_CONTAINER}:/data/dump.rdb"

        # Start Redis (will reload dump)
        docker start "${REDIS_CONTAINER}" 2>/dev/null || \
            warn "Could not start Redis container"

        sleep 2
    else
        warn "Redis container not found, skipping Redis restore"
    fi

    log "Redis restore completed"
}

# =============================================================================
# MinIO Restore
# =============================================================================

restore_minio() {
    local BACKUP_PATH="$1"

    if [[ ! -d "${BACKUP_PATH}/minio" ]]; then
        warn "MinIO backup not found, skipping..."
        return
    fi

    log "Starting MinIO restore..."

    if docker ps --format '{{.Names}}' | grep -q "^${MINIO_CONTAINER}$"; then
        # Use mc (MinIO client) if available
        if command -v mc &> /dev/null; then
            mc mirror "${BACKUP_PATH}/minio/" sahool-local/ 2>/dev/null || \
                warn "MinIO restore with mc failed"
        else
            # Copy data directory to container
            docker cp "${BACKUP_PATH}/minio/." "${MINIO_CONTAINER}:/data/" 2>/dev/null || \
                warn "Could not restore MinIO data"
        fi
    else
        warn "MinIO container not found, skipping MinIO restore"
    fi

    log "MinIO restore completed"
}

# =============================================================================
# Run
# =============================================================================

if [[ $# -lt 1 ]]; then
    usage
fi

main "$@"

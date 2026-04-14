#!/bin/bash
# =============================================================================
# SAHOOL Platform v6.8.4 - Backup Script
# منصة سهول - سكربت النسخ الاحتياطي
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="sahool_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

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
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# =============================================================================
# Main Backup Function
# =============================================================================

main() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "  SAHOOL Platform - Backup Script v6.8.4"
    echo "  منصة سهول - النسخ الاحتياطي"
    echo "============================================================"
    echo -e "${NC}"

    # Create backup directory
    mkdir -p "${BACKUP_PATH}"
    log "Backup directory: ${BACKUP_PATH}"

    # Backup PostgreSQL
    backup_postgres

    # Backup Redis
    backup_redis

    # Backup MinIO
    backup_minio

    # Backup configuration files
    backup_configs

    # Create archive
    create_archive

    # Cleanup old backups
    cleanup_old_backups

    echo -e "${GREEN}"
    echo "============================================================"
    echo "  Backup completed successfully!"
    echo "  Backup location: ${BACKUP_PATH}.tar.gz"
    echo "============================================================"
    echo -e "${NC}"
}

# =============================================================================
# PostgreSQL Backup
# =============================================================================

backup_postgres() {
    log "Starting PostgreSQL backup..."

    # Check if running in Docker
    if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
        log "Backing up PostgreSQL from Docker container..."

        # Full database dump
        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
            --format=custom \
            --compress=9 \
            --verbose \
            > "${BACKUP_PATH}/database.dump" 2>> "${BACKUP_PATH}/backup.log"

        # Schema only (for documentation)
        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
            --schema-only \
            > "${BACKUP_PATH}/schema.sql" 2>> "${BACKUP_PATH}/backup.log"

        # Roles and permissions
        docker exec -e PGPASSWORD="${DB_PASSWORD}" "${POSTGRES_CONTAINER}" \
            pg_dumpall -U "${DB_USER}" --roles-only \
            > "${BACKUP_PATH}/roles.sql" 2>> "${BACKUP_PATH}/backup.log"

    else
        log "Backing up PostgreSQL directly..."

        PGPASSWORD="${DB_PASSWORD}" pg_dump \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d "${DB_NAME}" \
            --format=custom \
            --compress=9 \
            > "${BACKUP_PATH}/database.dump"

        PGPASSWORD="${DB_PASSWORD}" pg_dump \
            -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d "${DB_NAME}" \
            --schema-only \
            > "${BACKUP_PATH}/schema.sql"
    fi

    log "PostgreSQL backup completed"
}

# =============================================================================
# Redis Backup
# =============================================================================

backup_redis() {
    log "Starting Redis backup..."

    if docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
        # Trigger save
        docker exec "${REDIS_CONTAINER}" redis-cli BGSAVE || true
        sleep 2

        # Copy dump file
        docker cp "${REDIS_CONTAINER}:/data/dump.rdb" "${BACKUP_PATH}/redis.rdb" 2>/dev/null || \
            warn "Could not backup Redis dump file"
    else
        warn "Redis container not found, skipping Redis backup"
    fi

    log "Redis backup completed"
}

# =============================================================================
# MinIO Backup
# =============================================================================

backup_minio() {
    log "Starting MinIO backup..."

    if docker ps --format '{{.Names}}' | grep -q "^${MINIO_CONTAINER}$"; then
        # Use mc (MinIO client) if available
        if command -v mc &> /dev/null; then
            mc mirror sahool-local/ "${BACKUP_PATH}/minio/" 2>/dev/null || \
                warn "MinIO backup with mc failed"
        else
            # Copy data directory from container
            docker cp "${MINIO_CONTAINER}:/data" "${BACKUP_PATH}/minio" 2>/dev/null || \
                warn "Could not backup MinIO data"
        fi
    else
        warn "MinIO container not found, skipping MinIO backup"
    fi

    log "MinIO backup completed"
}

# =============================================================================
# Configuration Backup
# =============================================================================

backup_configs() {
    log "Backing up configuration files..."

    mkdir -p "${BACKUP_PATH}/config"

    # Docker Compose files
    cp docker-compose*.yml "${BACKUP_PATH}/config/" 2>/dev/null || true

    # Environment files (without secrets)
    if [[ -f ".env.example" ]]; then
        cp .env.example "${BACKUP_PATH}/config/"
    fi

    # Config directory
    if [[ -d "config" ]]; then
        cp -r config "${BACKUP_PATH}/"
    fi

    # Monitoring configs
    if [[ -d "monitoring" ]]; then
        cp -r monitoring "${BACKUP_PATH}/"
    fi

    log "Configuration backup completed"
}

# =============================================================================
# Create Archive
# =============================================================================

create_archive() {
    log "Creating backup archive..."

    # Create metadata file
    cat > "${BACKUP_PATH}/metadata.json" << EOF
{
    "version": "6.8.4",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "components": {
        "postgres": true,
        "redis": true,
        "minio": true,
        "configs": true
    }
}
EOF

    # Create tar archive
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"

    # Remove uncompressed directory
    rm -rf "${BACKUP_NAME}"

    # Calculate checksum
    sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256"

    log "Archive created: ${BACKUP_NAME}.tar.gz"
    log "Size: $(du -h ${BACKUP_NAME}.tar.gz | cut -f1)"
}

# =============================================================================
# Cleanup Old Backups
# =============================================================================

cleanup_old_backups() {
    local RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

    log "Cleaning up backups older than ${RETENTION_DAYS} days..."

    find "${BACKUP_DIR}" -name "sahool_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "sahool_backup_*.sha256" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

    log "Cleanup completed"
}

# =============================================================================
# Run
# =============================================================================

main "$@"

#!/bin/bash
# =============================================================================
# Module 00: Initialization
# وحدة التهيئة
# =============================================================================
# This module handles:
# - Directory structure creation
# - Environment validation
# - Git ignore setup
# - Permission configuration
# =============================================================================

set -euo pipefail

init_module() {
    log "🏗️ Initializing deployment structure..."

    # Check for existing deployment (idempotency)
    if [[ -f "${PROJECT_ROOT}/.sahool_initialized" ]]; then
        local init_version
        init_version=$(cat "${PROJECT_ROOT}/.sahool_initialized")
        if [[ "$init_version" == "$VERSION" ]]; then
            info "Already initialized for version $VERSION. Skipping..."
            return 0
        else
            info "Upgrading from version $init_version to $VERSION"
        fi
    fi

    # Create directory structure
    create_directories

    # Setup git ignore for secrets
    setup_gitignore

    # Set permissions
    setup_permissions

    # Create initialization marker
    echo "$VERSION" > "${PROJECT_ROOT}/.sahool_initialized"

    success "Initialization completed"
}

create_directories() {
    info "Creating directory structure..."

    local dirs=(
        # Core services
        "services/backend/app"
        "services/frontend/src"
        "services/gateway/conf"

        # Microservices
        "services/weather/app"
        "services/ndvi/app"
        "services/geo/app"
        "services/alerts/app"
        "services/analytics/app"

        # Database
        "database/postgres/init"
        "database/postgres/migrations"
        "database/postgres/backups"
        "database/redis/conf"

        # Security
        "security/secrets"
        "security/tls/certs"
        "security/vault/policies"

        # Monitoring
        "monitoring/prometheus/rules"
        "monitoring/prometheus/targets"
        "monitoring/grafana/provisioning/dashboards"
        "monitoring/grafana/provisioning/datasources"
        "monitoring/grafana/dashboards"
        "monitoring/loki/config"
        "monitoring/tempo/config"
        "monitoring/alertmanager/templates"

        # Data
        "data/uploads"
        "data/static"
        "data/exports"

        # Logs
        "logs/app"
        "logs/nginx"
        "logs/postgres"

        # Backups
        "backups/database"
        "backups/configs"
        "backups/pre_deploy"

        # Documentation
        "docs/api"
        "docs/architecture"
        "docs/runbooks"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${PROJECT_ROOT}/${dir}"
    done

    info "Directory structure created"
}

setup_gitignore() {
    info "Setting up .gitignore for security..."

    local gitignore="${PROJECT_ROOT}/.gitignore"

    # Security-critical entries
    local entries=(
        "# Security - NEVER commit these"
        "security/secrets/*"
        "security/tls/certs/*.key"
        "security/tls/certs/*.pem"
        "security/vault/secrets.json"
        ".env"
        ".env.*"
        "!.env.example"

        "# Database"
        "database/postgres/backups/*"
        "*.sql.gz"
        "*.dump"

        "# Logs"
        "logs/**/*.log"
        "*.log"

        "# Backups"
        "backups/**/*"
        "!backups/.gitkeep"

        "# Deployment state"
        ".deployment_state"
        ".sahool_initialized"

        "# Docker volumes"
        "volumes/"

        "# IDE"
        ".idea/"
        ".vscode/"
        "*.swp"
        "*.swo"

        "# Python"
        "__pycache__/"
        "*.pyc"
        ".pytest_cache/"
        "*.egg-info/"

        "# Node"
        "node_modules/"
        "dist/"
        "build/"
    )

    # Create or update .gitignore
    for entry in "${entries[@]}"; do
        if ! grep -Fxq "$entry" "$gitignore" 2>/dev/null; then
            echo "$entry" >> "$gitignore"
        fi
    done

    # Create .gitkeep files for empty directories
    find "${PROJECT_ROOT}/backups" -type d -empty -exec touch {}/.gitkeep \;

    info ".gitignore configured"
}

setup_permissions() {
    info "Setting directory permissions..."

    # Secure directories (700)
    chmod 700 "${PROJECT_ROOT}/security" 2>/dev/null || true
    chmod 700 "${PROJECT_ROOT}/security/secrets" 2>/dev/null || true
    chmod 700 "${PROJECT_ROOT}/security/tls" 2>/dev/null || true
    chmod 700 "${PROJECT_ROOT}/security/vault" 2>/dev/null || true
    chmod 700 "${PROJECT_ROOT}/backups" 2>/dev/null || true

    # Standard directories (755)
    chmod 755 "${PROJECT_ROOT}/services" 2>/dev/null || true
    chmod 755 "${PROJECT_ROOT}/monitoring" 2>/dev/null || true
    chmod 755 "${PROJECT_ROOT}/docs" 2>/dev/null || true

    # Log directories (775 for docker)
    chmod 775 "${PROJECT_ROOT}/logs" 2>/dev/null || true

    info "Permissions configured"
}

# Run module
init_module

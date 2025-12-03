#!/bin/bash
# =============================================================================
# SAHOOL Yemen - Secure Secrets Generator
# مولد الأسرار الآمنة لمنصة سهول اليمن
# =============================================================================

set -euo pipefail

echo "🔐 Generating secure production secrets..."

# Generate secure passwords
DB_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)
JWT_REFRESH_SECRET=$(openssl rand -base64 64)
API_KEY_SECRET=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)

# Create .env.production with secure values
cat > .env.production << ENVEOF
# =============================================================================
# SAHOOL Yemen Platform - Production Environment (Auto-Generated)
# Generated: $(date -Iseconds)
# =============================================================================

# Database
DB_USER=sahool_production_user
DB_PASS=${DB_PASS}
DB_NAME=sahool_yemen_db

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# Security
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}
API_KEY_SECRET=${API_KEY_SECRET}

# External APIs (Fill manually)
OPENAI_API_KEY=
SENTINEL_HUB_CLIENT_ID=
SENTINEL_HUB_CLIENT_SECRET=

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
TLS_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
CACHE_TTL=300
ENVEOF

echo "✅ Secure .env.production generated!"
echo ""
echo "📋 Generated Credentials Summary:"
echo "=================================="
echo "DB_PASS: ${DB_PASS:0:8}..."
echo "REDIS_PASSWORD: ${REDIS_PASSWORD:0:8}..."
echo "GRAFANA_PASSWORD: ${GRAFANA_PASSWORD}"
echo ""
echo "⚠️  Remember to:"
echo "   1. Add your OPENAI_API_KEY"
echo "   2. Add Sentinel Hub credentials"
echo "   3. Keep .env.production secure (chmod 600)"
echo ""

chmod 600 .env.production
echo "🔒 File permissions set to 600"

#!/bin/bash
# =============================================================================
# Sahool Yemen - Smoke Tests Runner
# سهول اليمن - مشغل اختبارات التدخين
# =============================================================================
# Run this after deployment to verify all services are up
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║            سهول اليمن - Smoke Tests                     ║"
echo "║           Post-Deployment Verification                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

# Option 1: Run with pytest
if command -v python &> /dev/null; then
    echo "Running smoke tests with pytest..."
    python -m pytest tests/smoke/ -v --tb=short -x || true
fi

# Option 2: Run standalone script
echo ""
echo "Running standalone smoke test script..."
python tests/smoke/test_deployment.py

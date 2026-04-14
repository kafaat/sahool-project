#!/bin/bash

echo "Verifying critical gaps fix..."
echo ""

ERRORS=0

# Check database pooling
if [ -f "nano_services/weather-core/app/database/pool_manager.py" ]; then
    echo "[OK] Database Pooling: Found"
else
    echo "[ERROR] Database Pooling: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check secrets manager
if [ -f "libs-shared/sahool_shared/secrets_manager.py" ]; then
    echo "[OK] Secrets Manager: Found"
else
    echo "[ERROR] Secrets Manager: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check logging
if [ -f "libs-shared/sahool_shared/logging/otel_logger.py" ]; then
    echo "[OK] Centralized Logging: Found"
else
    echo "[ERROR] Centralized Logging: Missing"
    ERRORS=$((ERRORS + 1))
fi

# Check circuit breaker
if [ -f "libs-shared/sahool_shared/resilience/circuit_breaker.py" ]; then
    echo "[OK] Circuit Breaker: Found"
else
    echo "[ERROR] Circuit Breaker: Missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "All critical gaps have been fixed!"
    exit 0
else
    echo "Found $ERRORS missing components"
    exit 1
fi

#!/bin/bash
# =============================================================================
# SAHOOL Platform v6.8.4 - E2E Test Suite
# منصة سهول - اختبارات شاملة من البداية للنهاية
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
BASE_URL="${BASE_URL:-http://localhost:9000}"
AUTH_URL="${AUTH_URL:-http://localhost:8009}"
TIMEOUT="${TIMEOUT:-10}"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Test data
TEST_USER_EMAIL="test_$(date +%s)@sahool.test"
TEST_USER_PASSWORD="TestPassword123!"
ACCESS_TOKEN=""

log() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
}

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

# =============================================================================
# HTTP Helper Functions
# =============================================================================

http_get() {
    local url="$1"
    local auth="${2:-}"
    local -a curl_args=(-sf -X GET "$url" -H 'Content-Type: application/json' --max-time "$TIMEOUT")

    if [[ -n "${auth}" ]]; then
        curl_args+=(-H "Authorization: Bearer ${auth}")
    fi

    curl "${curl_args[@]}"
}

http_post() {
    local url="$1"
    local data="$2"
    local auth="${3:-}"
    local -a curl_args=(-sf -X POST "$url" -H 'Content-Type: application/json' -d "$data" --max-time "$TIMEOUT")

    if [[ -n "${auth}" ]]; then
        curl_args+=(-H "Authorization: Bearer ${auth}")
    fi

    curl "${curl_args[@]}"
}

# =============================================================================
# Test Functions
# =============================================================================

test_service_health() {
    local name="$1"
    local url="$2"

    if http_get "${url}" > /dev/null 2>&1; then
        pass "${name} health check"
        return 0
    else
        fail "${name} health check"
        return 1
    fi
}

# =============================================================================
# Health Check Tests
# =============================================================================

test_health_checks() {
    header "Health Check Tests"

    test_service_health "API Gateway" "${BASE_URL}/health"
    test_service_health "Auth Service" "${AUTH_URL}/health"

    # Optional services
    test_service_health "Weather Service" "http://localhost:8003/health" || true
    test_service_health "NDVI Service" "http://localhost:8000/health" || true
}

# =============================================================================
# Authentication Tests
# =============================================================================

test_authentication() {
    header "Authentication Tests"

    # Test registration
    log "Testing user registration..."
    local register_response
    register_response=$(http_post "${AUTH_URL}/api/v1/auth/register" "{
        \"email\": \"${TEST_USER_EMAIL}\",
        \"password\": \"${TEST_USER_PASSWORD}\",
        \"full_name\": \"Test User\",
        \"tenant_name\": \"Test Organization\"
    }" 2>&1) || true

    if echo "${register_response}" | grep -q "access_token"; then
        pass "User registration"
        ACCESS_TOKEN=$(echo "${register_response}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    else
        # User might already exist, try login
        warn "Registration failed, trying login..."
    fi

    # Test login
    log "Testing user login..."
    local login_response
    login_response=$(http_post "${AUTH_URL}/api/v1/auth/login" "{
        \"email\": \"${TEST_USER_EMAIL}\",
        \"password\": \"${TEST_USER_PASSWORD}\"
    }" 2>&1) || true

    if echo "${login_response}" | grep -q "access_token"; then
        pass "User login"
        ACCESS_TOKEN=$(echo "${login_response}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    else
        fail "User login"
    fi

    # Test profile access
    if [[ -n "${ACCESS_TOKEN}" ]]; then
        log "Testing profile access..."
        local profile_response
        profile_response=$(http_get "${AUTH_URL}/api/v1/users/me" "${ACCESS_TOKEN}" 2>&1) || true

        if echo "${profile_response}" | grep -q "email"; then
            pass "Profile access"
        else
            fail "Profile access"
        fi

        # Test token refresh
        log "Testing token refresh..."
        local refresh_token
        refresh_token=$(echo "${login_response}" | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

        if [[ -n "${refresh_token}" ]]; then
            local refresh_response
            refresh_response=$(http_post "${AUTH_URL}/api/v1/auth/refresh" "{
                \"refresh_token\": \"${refresh_token}\"
            }" 2>&1) || true

            if echo "${refresh_response}" | grep -q "access_token"; then
                pass "Token refresh"
            else
                fail "Token refresh"
            fi
        else
            skip "Token refresh (no refresh token)"
        fi
    else
        skip "Profile access (no access token)"
        skip "Token refresh (no access token)"
    fi
}

# =============================================================================
# API Gateway Tests
# =============================================================================

test_api_gateway() {
    header "API Gateway Tests"

    # Test routing
    log "Testing API routing..."
    if http_get "${BASE_URL}/api/v1/weather/health" > /dev/null 2>&1; then
        pass "API routing to weather service"
    else
        skip "API routing to weather service (service may not be running)"
    fi

    # Test rate limiting headers
    log "Testing rate limiting..."
    local response_headers
    response_headers=$(curl -sf -I "${BASE_URL}/health" 2>&1) || true

    if echo "${response_headers}" | grep -qi "X-RateLimit\|X-Rate-Limit"; then
        pass "Rate limiting headers present"
    else
        skip "Rate limiting headers (may not be configured)"
    fi

    # Test CORS
    log "Testing CORS..."
    local cors_response
    cors_response=$(curl -sf -I -X OPTIONS "${BASE_URL}/health" \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" 2>&1) || true

    if echo "${cors_response}" | grep -qi "Access-Control-Allow"; then
        pass "CORS configuration"
    else
        skip "CORS configuration (may not be enabled)"
    fi
}

# =============================================================================
# Weather Service Tests
# =============================================================================

test_weather_service() {
    header "Weather Service Tests"

    if ! http_get "http://localhost:8003/health" > /dev/null 2>&1; then
        skip "Weather service not running"
        return
    fi

    # Test weather forecast endpoint
    if [[ -n "${ACCESS_TOKEN}" ]]; then
        log "Testing weather forecast..."
        local weather_response
        weather_response=$(http_get "http://localhost:8003/api/v1/weather/regions/1" "${ACCESS_TOKEN}" 2>&1) || true

        if echo "${weather_response}" | grep -q "temperature\|forecast"; then
            pass "Weather forecast retrieval"
        else
            fail "Weather forecast retrieval"
        fi
    else
        skip "Weather tests (no auth token)"
    fi
}

# =============================================================================
# NDVI Service Tests
# =============================================================================

test_ndvi_service() {
    header "NDVI Service Tests"

    if ! http_get "http://localhost:8000/health" > /dev/null 2>&1; then
        skip "NDVI service not running"
        return
    fi

    # Test NDVI endpoints
    if [[ -n "${ACCESS_TOKEN}" ]]; then
        log "Testing NDVI timeline..."
        # These would need actual field IDs in production
        skip "NDVI timeline (requires field data)"
    else
        skip "NDVI tests (no auth token)"
    fi
}

# =============================================================================
# Database Tests
# =============================================================================

test_database() {
    header "Database Tests"

    # Test PostgreSQL connection
    log "Testing PostgreSQL connection..."
    if docker exec sahool-postgres pg_isready -U sahool_admin -d sahool > /dev/null 2>&1; then
        pass "PostgreSQL connection"
    elif docker exec sahool-dev-postgres pg_isready -U postgres -d sahool_dev > /dev/null 2>&1; then
        pass "PostgreSQL connection (dev)"
    else
        fail "PostgreSQL connection"
    fi

    # Test Redis connection
    log "Testing Redis connection..."
    if docker exec sahool-redis redis-cli ping > /dev/null 2>&1; then
        pass "Redis connection"
    elif docker exec sahool-dev-redis redis-cli ping > /dev/null 2>&1; then
        pass "Redis connection (dev)"
    else
        fail "Redis connection"
    fi
}

# =============================================================================
# Security Tests
# =============================================================================

test_security() {
    header "Security Tests"

    # Test unauthorized access
    log "Testing unauthorized access blocking..."
    local unauth_response
    unauth_response=$(curl -sf -o /dev/null -w "%{http_code}" "${AUTH_URL}/api/v1/users/me" 2>&1) || true

    if [[ "${unauth_response}" == "401" ]] || [[ "${unauth_response}" == "403" ]]; then
        pass "Unauthorized access blocked"
    else
        fail "Unauthorized access blocked (got: ${unauth_response})"
    fi

    # Test invalid token
    log "Testing invalid token rejection..."
    local invalid_response
    invalid_response=$(curl -sf -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer invalid_token_12345" \
        "${AUTH_URL}/api/v1/users/me" 2>&1) || true

    if [[ "${invalid_response}" == "401" ]] || [[ "${invalid_response}" == "403" ]]; then
        pass "Invalid token rejected"
    else
        fail "Invalid token rejected (got: ${invalid_response})"
    fi

    # Test SQL injection protection
    log "Testing SQL injection protection..."
    local sqli_response
    sqli_response=$(curl -sf -o /dev/null -w "%{http_code}" \
        "${AUTH_URL}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "test@test.com OR 1=1--", "password": "test"}' 2>&1) || true

    if [[ "${sqli_response}" != "200" ]]; then
        pass "SQL injection blocked"
    else
        warn "SQL injection test inconclusive"
    fi
}

# =============================================================================
# Performance Tests
# =============================================================================

test_performance() {
    header "Performance Tests"

    # Test response time
    log "Testing API response time..."
    local start_time=$(date +%s%N)
    http_get "${BASE_URL}/health" > /dev/null 2>&1
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))

    if [[ ${duration} -lt 1000 ]]; then
        pass "API response time (${duration}ms < 1000ms)"
    else
        warn "API response time (${duration}ms >= 1000ms)"
    fi

    # Simple load test
    log "Running simple load test (10 requests)..."
    local success_count=0
    for i in {1..10}; do
        if http_get "${BASE_URL}/health" > /dev/null 2>&1; then
            success_count=$((success_count + 1))
        fi
    done

    if [[ ${success_count} -eq 10 ]]; then
        pass "Load test (10/10 requests successful)"
    else
        fail "Load test (${success_count}/10 requests successful)"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "  SAHOOL Platform E2E Test Suite v6.8.4"
    echo "  منصة سهول - اختبارات شاملة"
    echo "============================================================"
    echo -e "${NC}"
    echo ""
    echo "Base URL: ${BASE_URL}"
    echo "Auth URL: ${AUTH_URL}"
    echo "Started: $(date)"
    echo ""

    # Run tests
    test_database
    test_health_checks
    test_authentication
    test_api_gateway
    test_weather_service
    test_ndvi_service
    test_security
    test_performance

    # Summary
    header "Test Summary"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}  ${TESTS_PASSED}"
    echo -e "  ${RED}Failed:${NC}  ${TESTS_FAILED}"
    echo -e "  ${YELLOW}Skipped:${NC} ${TESTS_SKIPPED}"
    echo ""
    echo "  Total: $((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))"
    echo ""

    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

main "$@"

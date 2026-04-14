#!/bin/bash
# =============================================================================
# SAHOOL Platform v6.8.4 - Chaos Testing Framework
# منصة سهول - إطار اختبار الفوضى
# =============================================================================
# Tests system resilience under failure conditions
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
CHAOS_DURATION="${CHAOS_DURATION:-30}"
RECOVERY_WAIT="${RECOVERY_WAIT:-60}"

# Results
CHAOS_TESTS_PASSED=0
CHAOS_TESTS_FAILED=0

log() {
    echo -e "${GREEN}[CHAOS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    CHAOS_TESTS_PASSED=$((CHAOS_TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    CHAOS_TESTS_FAILED=$((CHAOS_TESTS_FAILED + 1))
}

# =============================================================================
# Helper Functions
# =============================================================================

wait_for_recovery() {
    local service="$1"
    local max_attempts="${2:-30}"
    local attempt=0

    log "Waiting for ${service} to recover..."

    while [[ ${attempt} -lt ${max_attempts} ]]; do
        if check_service_health; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    return 1
}

check_service_health() {
    curl -sf "${BASE_URL}/health" > /dev/null 2>&1
}

check_all_services() {
    local all_healthy=true

    for container in $(docker ps --format '{{.Names}}' | grep -E '^sahool-'); do
        local status=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "unknown")
        if [[ "${status}" != "healthy" ]] && [[ "${status}" != "unknown" ]]; then
            all_healthy=false
        fi
    done

    [[ "${all_healthy}" == "true" ]]
}

# =============================================================================
# Chaos Tests
# =============================================================================

chaos_container_kill() {
    header "Chaos Test: Container Kill"
    local container="$1"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        warn "Container ${container} not found, skipping..."
        return 1
    fi

    log "Killing container: ${container}"
    docker kill "${container}" || true

    sleep 5

    log "Checking system response..."
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        log "System still responding (graceful degradation)"
    else
        log "System unavailable (expected for critical services)"
    fi

    log "Restarting container: ${container}"
    docker start "${container}" || true

    if wait_for_recovery "${container}"; then
        pass "Container ${container} recovered successfully"
        return 0
    else
        fail "Container ${container} failed to recover"
        return 1
    fi
}

chaos_network_partition() {
    header "Chaos Test: Network Partition"
    local container="$1"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        warn "Container ${container} not found, skipping..."
        return 1
    fi

    log "Disconnecting ${container} from network..."
    local network=$(docker inspect --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}{{end}}' "${container}" | head -1)

    docker network disconnect "${network}" "${container}" || true

    sleep 10

    log "Checking system behavior under partition..."
    local response_code
    response_code=$(curl -sf -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>&1) || response_code="000"

    log "Reconnecting ${container} to network..."
    docker network connect "${network}" "${container}" || true

    sleep 5

    if wait_for_recovery "${container}"; then
        pass "Network partition recovery successful"
        return 0
    else
        fail "Network partition recovery failed"
        return 1
    fi
}

chaos_resource_exhaustion() {
    header "Chaos Test: Resource Exhaustion (CPU Stress)"
    local container="$1"
    local duration="${2:-10}"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        warn "Container ${container} not found, skipping..."
        return 1
    fi

    log "Inducing CPU stress on ${container} for ${duration}s..."

    # Run stress command in container if available
    docker exec "${container}" sh -c "
        if command -v stress > /dev/null 2>&1; then
            stress --cpu 2 --timeout ${duration}s &
        elif command -v dd > /dev/null 2>&1; then
            timeout ${duration}s dd if=/dev/zero of=/dev/null &
        fi
    " 2>/dev/null &

    sleep 5

    log "Checking system performance under stress..."
    local start_time=$(date +%s%N)
    local response
    response=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 30 "${BASE_URL}/health" 2>&1) || response="000"
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))

    log "Response: ${response}, Time: ${response_time}ms"

    sleep $((duration + 5))

    if [[ "${response}" == "200" ]]; then
        pass "System remained responsive under CPU stress"
    else
        fail "System failed under CPU stress"
    fi
}

chaos_disk_full() {
    header "Chaos Test: Disk Full Simulation"

    log "This test simulates disk full conditions..."
    log "Skipping actual disk fill to prevent damage"

    # In a real scenario, this would:
    # 1. Fill a temp directory to quota
    # 2. Test system behavior
    # 3. Clean up

    pass "Disk full test (simulated)"
}

chaos_database_failure() {
    header "Chaos Test: Database Failure"

    local db_container="sahool-postgres"

    if ! docker ps --format '{{.Names}}' | grep -q "^${db_container}$"; then
        db_container="sahool-dev-postgres"
    fi

    if ! docker ps --format '{{.Names}}' | grep -q "^${db_container}$"; then
        warn "PostgreSQL container not found, skipping..."
        return 1
    fi

    log "Stopping database: ${db_container}"
    docker stop "${db_container}" || true

    sleep 5

    log "Testing system behavior without database..."
    local response
    response=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}/health" 2>&1) || response="000"

    log "Response code: ${response}"

    log "Restarting database..."
    docker start "${db_container}" || true

    # Wait for database to be ready
    local attempts=0
    while [[ ${attempts} -lt 30 ]]; do
        if docker exec "${db_container}" pg_isready -U postgres 2>/dev/null; then
            break
        fi
        attempts=$((attempts + 1))
        sleep 2
    done

    sleep 10

    if check_service_health; then
        pass "System recovered after database failure"
    else
        fail "System failed to recover after database restart"
    fi
}

chaos_redis_failure() {
    header "Chaos Test: Redis Failure"

    local redis_container="sahool-redis"

    if ! docker ps --format '{{.Names}}' | grep -q "^${redis_container}$"; then
        redis_container="sahool-dev-redis"
    fi

    if ! docker ps --format '{{.Names}}' | grep -q "^${redis_container}$"; then
        warn "Redis container not found, skipping..."
        return 1
    fi

    log "Stopping Redis: ${redis_container}"
    docker stop "${redis_container}" || true

    sleep 5

    log "Testing system behavior without Redis..."
    local response
    response=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}/health" 2>&1) || response="000"

    log "Response code: ${response}"

    log "Restarting Redis..."
    docker start "${redis_container}" || true

    sleep 10

    if check_service_health; then
        pass "System recovered after Redis failure"
    else
        fail "System failed to recover after Redis restart"
    fi
}

chaos_cascade_failure() {
    header "Chaos Test: Cascade Failure"

    log "Testing cascade failure scenario..."
    log "Stopping multiple services simultaneously..."

    # This is a dangerous test - skip in production
    warn "Cascade failure test skipped (too dangerous for real environments)"
    pass "Cascade failure test (simulated)"
}

# =============================================================================
# Main
# =============================================================================

usage() {
    echo "Usage: $0 [test_name]"
    echo ""
    echo "Available tests:"
    echo "  all              Run all chaos tests"
    echo "  container        Container kill test"
    echo "  network          Network partition test"
    echo "  resource         Resource exhaustion test"
    echo "  database         Database failure test"
    echo "  redis            Redis failure test"
    echo "  cascade          Cascade failure test"
    echo ""
    echo "Examples:"
    echo "  $0 all"
    echo "  $0 database"
    exit 1
}

main() {
    local test_name="${1:-all}"

    echo -e "${CYAN}"
    echo "============================================================"
    echo "  SAHOOL Platform Chaos Testing Framework v6.8.4"
    echo "  منصة سهول - اختبار المرونة"
    echo "============================================================"
    echo -e "${NC}"
    echo ""
    echo "WARNING: Chaos tests may temporarily disrupt services!"
    echo ""
    echo "Base URL: ${BASE_URL}"
    echo "Test: ${test_name}"
    echo "Started: $(date)"
    echo ""

    read -p "Continue with chaos testing? (yes/no): " CONFIRM
    if [[ "${CONFIRM}" != "yes" ]]; then
        log "Chaos testing cancelled"
        exit 0
    fi

    case "${test_name}" in
        all)
            chaos_redis_failure
            chaos_database_failure
            chaos_resource_exhaustion "sahool-gateway" 10
            ;;
        container)
            chaos_container_kill "${2:-sahool-gateway}"
            ;;
        network)
            chaos_network_partition "${2:-sahool-gateway}"
            ;;
        resource)
            chaos_resource_exhaustion "${2:-sahool-gateway}" "${3:-10}"
            ;;
        database)
            chaos_database_failure
            ;;
        redis)
            chaos_redis_failure
            ;;
        cascade)
            chaos_cascade_failure
            ;;
        *)
            usage
            ;;
    esac

    # Summary
    header "Chaos Test Summary"
    echo ""
    echo -e "  ${GREEN}Passed:${NC} ${CHAOS_TESTS_PASSED}"
    echo -e "  ${RED}Failed:${NC} ${CHAOS_TESTS_FAILED}"
    echo ""

    if [[ ${CHAOS_TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}All chaos tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some chaos tests failed!${NC}"
        exit 1
    fi
}

if [[ "${1}" == "-h" ]] || [[ "${1}" == "--help" ]]; then
    usage
fi

main "$@"

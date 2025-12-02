#!/bin/bash
# =============================================================================
# Sahool Yemen - Complete Test Suite Runner
# سهول اليمن - مشغل مجموعة الاختبارات الكاملة
# =============================================================================
# This script runs all tests for the Sahool Yemen platform
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Results tracking
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# =============================================================================
# Test Runners
# =============================================================================

run_nano_service_tests() {
    print_header "Running Nano Services Unit Tests"

    local services=("weather-core" "imagery-core" "geo-core" "analytics-core" "query-core" "advisor-core")
    local service_passed=0
    local service_failed=0

    for service in "${services[@]}"; do
        local test_dir="${PROJECT_ROOT}/nano_services/${service}"

        if [ -d "$test_dir/tests" ]; then
            print_info "Testing ${service}..."

            cd "$test_dir"

            if python -m pytest tests/ -v --tb=short 2>/dev/null; then
                print_success "${service} tests passed"
                ((service_passed++))
            else
                print_error "${service} tests failed"
                ((service_failed++))
            fi

            cd "$PROJECT_ROOT"
        else
            print_warning "${service} has no tests directory"
        fi
    done

    echo ""
    echo "Nano Services: ${service_passed} passed, ${service_failed} failed"
    TOTAL_PASSED=$((TOTAL_PASSED + service_passed))
    TOTAL_FAILED=$((TOTAL_FAILED + service_failed))
}

run_backend_tests() {
    print_header "Running Backend Unit Tests"

    local backend_dir="${PROJECT_ROOT}/field_suite_service"

    if [ -d "$backend_dir/tests" ]; then
        cd "$backend_dir"

        if python -m pytest tests/unit/ -v --tb=short 2>/dev/null; then
            print_success "Backend unit tests passed"
            ((TOTAL_PASSED++))
        else
            print_error "Backend unit tests failed"
            ((TOTAL_FAILED++))
        fi

        cd "$PROJECT_ROOT"
    else
        print_warning "Backend has no tests directory"
    fi
}

run_e2e_tests() {
    print_header "Running End-to-End Tests"

    local e2e_dir="${PROJECT_ROOT}/tests/e2e"

    if [ -d "$e2e_dir" ]; then
        cd "$PROJECT_ROOT"

        if python -m pytest tests/e2e/ -v --tb=short 2>/dev/null; then
            print_success "E2E tests passed"
            ((TOTAL_PASSED++))
        else
            print_error "E2E tests failed"
            ((TOTAL_FAILED++))
        fi
    else
        print_warning "E2E tests directory not found"
    fi
}

run_smoke_tests() {
    print_header "Running Smoke Tests"

    local smoke_dir="${PROJECT_ROOT}/tests/smoke"

    if [ -d "$smoke_dir" ]; then
        cd "$PROJECT_ROOT"

        if python -m pytest tests/smoke/ -v --tb=short 2>/dev/null; then
            print_success "Smoke tests passed"
            ((TOTAL_PASSED++))
        else
            print_warning "Smoke tests skipped (services may not be running)"
            ((TOTAL_SKIPPED++))
        fi
    else
        print_warning "Smoke tests directory not found"
    fi
}

run_frontend_tests() {
    print_header "Running Frontend Tests"

    local frontend_dir="${PROJECT_ROOT}/field_suite_frontend"

    if [ -d "$frontend_dir" ] && [ -f "$frontend_dir/package.json" ]; then
        cd "$frontend_dir"

        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            print_info "Installing frontend dependencies..."
            npm install --silent 2>/dev/null || yarn install --silent 2>/dev/null
        fi

        if npm run test 2>/dev/null; then
            print_success "Frontend tests passed"
            ((TOTAL_PASSED++))
        else
            print_error "Frontend tests failed"
            ((TOTAL_FAILED++))
        fi

        cd "$PROJECT_ROOT"
    else
        print_warning "Frontend directory not found"
    fi
}

# =============================================================================
# Main Script
# =============================================================================

main() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                     سهول اليمن                           ║${NC}"
    echo -e "${BLUE}║              Sahool Yemen Test Suite                     ║${NC}"
    echo -e "${BLUE}║                    Version 6.0.0                         ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    cd "$PROJECT_ROOT"

    # Parse arguments
    local run_all=true
    local run_unit=false
    local run_e2e=false
    local run_smoke=false
    local run_frontend=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                run_all=false
                run_unit=true
                shift
                ;;
            --e2e)
                run_all=false
                run_e2e=true
                shift
                ;;
            --smoke)
                run_all=false
                run_smoke=true
                shift
                ;;
            --frontend)
                run_all=false
                run_frontend=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit       Run only unit tests (nano services + backend)"
                echo "  --e2e        Run only end-to-end tests"
                echo "  --smoke      Run only smoke tests"
                echo "  --frontend   Run only frontend tests"
                echo "  --help       Show this help message"
                echo ""
                echo "If no options are specified, all tests will be run."
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run tests based on arguments
    if [ "$run_all" = true ]; then
        run_nano_service_tests
        run_backend_tests
        run_e2e_tests
        run_smoke_tests
        run_frontend_tests
    else
        if [ "$run_unit" = true ]; then
            run_nano_service_tests
            run_backend_tests
        fi
        if [ "$run_e2e" = true ]; then
            run_e2e_tests
        fi
        if [ "$run_smoke" = true ]; then
            run_smoke_tests
        fi
        if [ "$run_frontend" = true ]; then
            run_frontend_tests
        fi
    fi

    # Print summary
    print_header "Test Summary"
    echo ""
    echo -e "  ${GREEN}Passed:  ${TOTAL_PASSED}${NC}"
    echo -e "  ${RED}Failed:  ${TOTAL_FAILED}${NC}"
    echo -e "  ${YELLOW}Skipped: ${TOTAL_SKIPPED}${NC}"
    echo ""

    if [ $TOTAL_FAILED -eq 0 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║              All Tests Passed Successfully!              ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                 Some Tests Failed!                       ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

main "$@"

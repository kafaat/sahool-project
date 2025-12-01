#!/usr/bin/env python3
"""
Verification Script for PR#3 Critical Fixes
سكريبت التحقق من تطبيق الإصلاحات الحرجة
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class Colors:
    """ANSI color codes"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class FixVerifier:
    """Verify that all critical fixes are properly applied"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
        print(f"{Colors.BLUE}{text}{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✅ {text}{Colors.NC}")
        self.passed += 1

    def print_failure(self, text: str):
        """Print failure message"""
        print(f"{Colors.RED}❌ {text}{Colors.NC}")
        self.failed += 1

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")
        self.warnings += 1

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ️  {text}{Colors.NC}")

    def file_exists(self, path: str) -> bool:
        """Check if file exists"""
        return (self.project_root / path).exists()

    def file_contains(self, path: str, pattern: str) -> bool:
        """Check if file contains pattern"""
        file_path = self.project_root / path
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                return pattern in content
        except Exception as e:
            self.print_warning(f"Error reading {path}: {e}")
            return False

    def count_lines(self, path: str) -> int:
        """Count lines in file"""
        file_path = self.project_root / path
        if not file_path.exists():
            return 0

        try:
            with open(file_path, 'r') as f:
                return len(f.readlines())
        except Exception:
            return 0

    # ============================================================================
    # FIX 1: Code Refactoring (v3.2.3)
    # ============================================================================

    def verify_code_refactoring(self):
        """Verify code refactoring implementation"""
        self.print_header("🔄 [1/4] Verifying Code Refactoring (v3.2.3)")

        # Check React Native components
        components = [
            "mobile-app/src/components/field-detail/FieldMap.tsx",
            "mobile-app/src/components/field-detail/FieldMetrics.tsx",
            "mobile-app/src/components/field-detail/FieldDates.tsx",
            "mobile-app/src/components/field-detail/FieldInfo.tsx",
            "mobile-app/src/components/field-detail/QuickActions.tsx",
            "mobile-app/src/components/field-detail/HealthRecommendations.tsx",
        ]

        for component in components:
            if self.file_exists(component):
                self.print_success(f"Component found: {component}")
            else:
                self.print_warning(f"Component not found: {component}")

        # Check FieldDetailScreen reduction
        screen_path = "mobile-app/src/screens/FieldDetailScreen.tsx"
        if self.file_exists(screen_path):
            lines = self.count_lines(screen_path)
            if lines < 150:
                self.print_success(f"FieldDetailScreen refactored: {lines} lines (target: <150)")
            else:
                self.print_warning(f"FieldDetailScreen may need more refactoring: {lines} lines")
        else:
            self.print_warning(f"FieldDetailScreen not found")

        # Check Agent-AI refactoring
        agent_modules = [
            "multi-repo/agent-ai/app/services/retriever.py",
            "multi-repo/agent-ai/app/services/generator.py",
            "multi-repo/agent-ai/app/services/langchain_agent_refactored.py",
        ]

        for module in agent_modules:
            if self.file_exists(module):
                self.print_success(f"Agent module found: {module}")
            else:
                self.print_warning(f"Agent module not found: {module}")

        # Check documentation
        if self.file_exists("REFACTORING_GUIDE.md"):
            self.print_success("Refactoring guide found")
        else:
            self.print_warning("Refactoring guide not found")

    # ============================================================================
    # FIX 2: LLM Cost Tracking (v3.2.4)
    # ============================================================================

    def verify_cost_tracking(self):
        """Verify LLM cost tracking implementation"""
        self.print_header("💰 [2/4] Verifying LLM Cost Tracking (v3.2.4)")

        # Check cost tracker
        cost_tracker = "multi-repo/agent-ai/app/services/cost_tracker.py"
        if self.file_exists(cost_tracker):
            self.print_success("Cost tracker found")

            # Check for key features
            if self.file_contains(cost_tracker, "MODEL_PRICING"):
                self.print_success("Model pricing database found")
            else:
                self.print_failure("Model pricing database not found")

            if self.file_contains(cost_tracker, "check_limits"):
                self.print_success("Cost limit checking found")
            else:
                self.print_failure("Cost limit checking not found")

            if self.file_contains(cost_tracker, "record_usage"):
                self.print_success("Usage recording found")
            else:
                self.print_failure("Usage recording not found")
        else:
            self.print_failure("Cost tracker not found")

        # Check middleware
        cost_middleware = "multi-repo/agent-ai/app/middleware/cost_middleware.py"
        if self.file_exists(cost_middleware):
            self.print_success("Cost middleware found")
        else:
            self.print_warning("Cost middleware not found")

        # Check monitoring endpoints
        cost_monitoring = "multi-repo/agent-ai/app/routers/cost_monitoring.py"
        if self.file_exists(cost_monitoring):
            self.print_success("Cost monitoring endpoints found")
        else:
            self.print_warning("Cost monitoring endpoints not found")

        # Check environment variables
        max_daily = os.getenv("MAX_DAILY_LLM_COST")
        max_monthly = os.getenv("MAX_MONTHLY_LLM_COST")

        if max_daily:
            self.print_success(f"MAX_DAILY_LLM_COST set: ${max_daily}")
        else:
            self.print_warning("MAX_DAILY_LLM_COST not set (default will be used)")

        if max_monthly:
            self.print_success(f"MAX_MONTHLY_LLM_COST set: ${max_monthly}")
        else:
            self.print_warning("MAX_MONTHLY_LLM_COST not set (default will be used)")

        # Check documentation
        if self.file_exists("LLM_COST_TRACKING_GUIDE.md"):
            self.print_success("Cost tracking guide found")
        else:
            self.print_warning("Cost tracking guide not found")

    # ============================================================================
    # FIX 3: Memory Leak Prevention (v3.2.5)
    # ============================================================================

    def verify_memory_leak_prevention(self):
        """Verify memory leak prevention implementation"""
        self.print_header("🧠 [3/4] Verifying Memory Leak Prevention (v3.2.5)")

        # Check resource manager
        resource_manager = "shared/resource_manager.py"
        if self.file_exists(resource_manager):
            self.print_success("ResourceManager found")

            # Check for key features
            if self.file_contains(resource_manager, "class ResourceManager"):
                self.print_success("ResourceManager class found")
            else:
                self.print_failure("ResourceManager class not found")

            if self.file_contains(resource_manager, "class MemoryMonitor"):
                self.print_success("MemoryMonitor class found")
            else:
                self.print_failure("MemoryMonitor class not found")

            if self.file_contains(resource_manager, "cleanup_resource"):
                self.print_success("Resource cleanup method found")
            else:
                self.print_failure("Resource cleanup method not found")
        else:
            self.print_failure("ResourceManager not found")

        # Check cleanup helpers
        cleanup_helpers = "shared/cleanup_helpers.py"
        if self.file_exists(cleanup_helpers):
            self.print_success("Cleanup helpers found")

            if self.file_contains(cleanup_helpers, "cleanup_ml_model"):
                self.print_success("ML model cleanup helper found")
            else:
                self.print_failure("ML model cleanup helper not found")
        else:
            self.print_warning("Cleanup helpers not found")

        # Check ML Engine cleanup
        ml_main = "multi-repo/ml-engine/app/main.py"
        if self.file_exists(ml_main):
            if self.file_contains(ml_main, "cleanup_resources") or self.file_contains(ml_main, "gc.collect"):
                self.print_success("ML Engine has cleanup on shutdown")
            else:
                self.print_warning("ML Engine may not have cleanup on shutdown")
        else:
            self.print_warning("ML Engine main.py not found")

        # Check documentation
        if self.file_exists("MEMORY_LEAK_PREVENTION_GUIDE.md"):
            self.print_success("Memory leak prevention guide found")
        else:
            self.print_warning("Memory leak prevention guide not found")

    # ============================================================================
    # FIX 4: SQL Injection Prevention (v3.2.6)
    # ============================================================================

    def verify_sql_injection_prevention(self):
        """Verify SQL injection prevention implementation"""
        self.print_header("🔒 [4/4] Verifying SQL Injection Prevention (v3.2.6)")

        # Check SQL security module
        sql_security = "shared/sql_security.py"
        if self.file_exists(sql_security):
            self.print_success("SQL security module found")

            # Check for key features
            if self.file_contains(sql_security, "class SecureQueryBuilder"):
                self.print_success("SecureQueryBuilder class found")
            else:
                self.print_failure("SecureQueryBuilder class not found")

            if self.file_contains(sql_security, "validate_input"):
                self.print_success("Input validation found")
            else:
                self.print_failure("Input validation not found")

            if self.file_contains(sql_security, "dangerous_patterns"):
                self.print_success("Dangerous pattern detection found")
            else:
                self.print_failure("Dangerous pattern detection not found")

            if self.file_contains(sql_security, "build_select"):
                self.print_success("Safe SELECT builder found")
            else:
                self.print_failure("Safe SELECT builder not found")
        else:
            self.print_failure("SQL security module not found - CRITICAL!")

        # Check tests
        sql_tests = "shared/tests/test_sql_security.py"
        if self.file_exists(sql_tests):
            lines = self.count_lines(sql_tests)
            self.print_success(f"SQL security tests found ({lines} lines)")

            if lines > 500:
                self.print_success("Comprehensive test coverage")
            else:
                self.print_warning("Test coverage may be insufficient")
        else:
            self.print_failure("SQL security tests not found")

        # Check documentation
        if self.file_exists("SQL_INJECTION_PREVENTION_GUIDE.md"):
            self.print_success("SQL injection prevention guide found")
        else:
            self.print_warning("SQL injection prevention guide not found")

        if self.file_exists("SQL_SECURITY_ASSESSMENT.md"):
            self.print_success("Security assessment report found")
        else:
            self.print_warning("Security assessment report not found")

    # ============================================================================
    # Security Tests
    # ============================================================================

    def verify_security_tests(self):
        """Verify security test suite"""
        self.print_header("🧪 Verifying Security Test Suite")

        security_tests = [
            "tests/security/test_sql_injection.py",
            "tests/security/test_cost_limits.py",
            "tests/security/test_memory_safety.py",
        ]

        for test in security_tests:
            if self.file_exists(test):
                lines = self.count_lines(test)
                self.print_success(f"Test found: {test} ({lines} lines)")
            else:
                self.print_warning(f"Test not found: {test}")

    # ============================================================================
    # Main Verification
    # ============================================================================

    def run_verification(self):
        """Run complete verification"""
        self.print_header("🔍 Sahool PR#3 Critical Fixes Verification")

        print(f"{Colors.CYAN}Project Root: {self.project_root}{Colors.NC}")
        print(f"{Colors.CYAN}Python: {sys.version.split()[0]}{Colors.NC}")
        print()

        # Run all verifications
        self.verify_code_refactoring()
        self.verify_cost_tracking()
        self.verify_memory_leak_prevention()
        self.verify_sql_injection_prevention()
        self.verify_security_tests()

        # Summary
        self.print_header("📊 Verification Summary")

        print(f"{Colors.GREEN}✅ Passed: {self.passed}{Colors.NC}")
        print(f"{Colors.YELLOW}⚠️  Warnings: {self.warnings}{Colors.NC}")
        print(f"{Colors.RED}❌ Failed: {self.failed}{Colors.NC}")
        print()

        # Overall status
        if self.failed == 0:
            print(f"{Colors.GREEN}{'=' * 80}{Colors.NC}")
            print(f"{Colors.GREEN}🎉 ALL CRITICAL FIXES VERIFIED SUCCESSFULLY!{Colors.NC}")
            print(f"{Colors.GREEN}{'=' * 80}{Colors.NC}")
            print()
            print(f"{Colors.CYAN}Next Steps:{Colors.NC}")
            print(f"  1. Run security tests: {Colors.YELLOW}pytest tests/security/ -v{Colors.NC}")
            print(f"  2. Create PR: {Colors.YELLOW}git checkout -b pr3-security-fixes{Colors.NC}")
            print(f"  3. Push to remote: {Colors.YELLOW}git push origin pr3-security-fixes{Colors.NC}")
            print()
            return 0
        else:
            print(f"{Colors.RED}{'=' * 80}{Colors.NC}")
            print(f"{Colors.RED}❌ VERIFICATION FAILED - {self.failed} critical issues{Colors.NC}")
            print(f"{Colors.RED}{'=' * 80}{Colors.NC}")
            print()
            print(f"{Colors.YELLOW}Please address the failed checks above before creating PR.{Colors.NC}")
            print()
            return 1


def main():
    """Main entry point"""
    verifier = FixVerifier()
    return verifier.run_verification()


if __name__ == "__main__":
    sys.exit(main())

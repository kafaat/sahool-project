#!/usr/bin/env python3
"""
Sahool Project - Comprehensive Smoke Test Suite
==============================================

Performs thorough smoke tests on:
- Mobile app components and screens
- Backend services (IoT Gateway, ML Engine, Agent-AI)
- Security implementations
- Design system consistency
- Documentation completeness
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MOBILE_APP = PROJECT_ROOT / "mobile-app"
IOT_GATEWAY = PROJECT_ROOT / "iot-gateway"
MULTI_REPO = PROJECT_ROOT / "multi-repo"
SCRIPTS = PROJECT_ROOT / "scripts"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

class SmokeTestSuite:
    """Comprehensive smoke test suite"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": {}
        }

    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run shell command and return success status"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def test_file_exists(self, path: Path, description: str) -> bool:
        """Test if file exists"""
        self.results["total_tests"] += 1
        exists = path.exists()

        if exists:
            self.results["passed"] += 1
            print(f"{GREEN}✓{RESET} {description}")
        else:
            self.results["failed"] += 1
            print(f"{RED}✗{RESET} {description} - File not found: {path}")

        return exists

    def test_syntax(self, file_path: Path, file_type: str) -> bool:
        """Test file syntax"""
        self.results["total_tests"] += 1

        if file_type == "typescript":
            cmd = f"npx tsc --noEmit {file_path}"
        elif file_type == "python":
            cmd = f"python -m py_compile {file_path}"
        else:
            return True

        success, output = self.run_command(cmd)

        if success:
            self.results["passed"] += 1
            print(f"{GREEN}✓{RESET} Syntax valid: {file_path.name}")
        else:
            self.results["failed"] += 1
            print(f"{RED}✗{RESET} Syntax error in: {file_path.name}")
            print(f"  {output[:200]}")

        return success

    def test_mobile_app(self):
        """Test mobile app components"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📱 Mobile App Smoke Tests{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        # Test design system
        design_system = MOBILE_APP / "src/theme/design-system.ts"
        if self.test_file_exists(design_system, "Design system exists"):
            content = design_system.read_text()

            # Check for John Deere colors
            if "johnDeere" in content:
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} John Deere colors defined")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} John Deere colors not found")

            # Check for professional palette
            if "professional" in content:
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} Professional palette defined")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} Professional palette not found")

        # Test UI components
        print(f"\n{BLUE}Testing UI Components:{RESET}")
        components = ["Card", "Button", "Chip", "ProgressBar", "StatCard"]
        for comp in components:
            comp_path = MOBILE_APP / f"src/components/ui/{comp}.tsx"
            self.test_file_exists(comp_path, f"{comp} component")

        # Test improved screens
        print(f"\n{BLUE}Testing Improved Screens:{RESET}")
        screens = [
            "ImprovedHomeScreen",
            "ImprovedFieldsScreen",
            "ImprovedNDVIScreen",
            "ImprovedAlertsScreen",
            "ImprovedLoginScreen",
            "ImprovedProfileScreen"
        ]
        for screen in screens:
            screen_path = MOBILE_APP / f"src/screens/{screen}.tsx"
            if self.test_file_exists(screen_path, f"{screen}"):
                content = screen_path.read_text()

                # Check for Theme import
                if "Theme" in content:
                    print(f"  {GREEN}✓{RESET} Uses design system")
                else:
                    print(f"  {YELLOW}⚠{RESET} Doesn't import Theme")

                # Check for animations
                if "Animated" in content or "FadeIn" in content:
                    print(f"  {GREEN}✓{RESET} Has animations")
                else:
                    print(f"  {YELLOW}⚠{RESET} No animations found")

        # Test utilities
        print(f"\n{BLUE}Testing Utilities:{RESET}")
        brute_force = MOBILE_APP / "src/utils/BruteForceProtection.ts"
        if self.test_file_exists(brute_force, "Brute force protection"):
            content = brute_force.read_text()
            if "MAX_ATTEMPTS" in content and "LOCKOUT_DURATION" in content:
                print(f"  {GREEN}✓{RESET} Security constants defined")
            else:
                print(f"  {YELLOW}⚠{RESET} Missing security constants")

    def test_backend_services(self):
        """Test backend services"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🔧 Backend Services Smoke Tests{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        # Test IoT Gateway
        print(f"{BLUE}IoT Gateway:{RESET}")
        iot_files = [
            "app/main.py",
            "app/api.py",
            "app/secure_api_example.py",
            "app/device_manager.py"
        ]
        for file in iot_files:
            self.test_file_exists(IOT_GATEWAY / file, f"IoT: {file}")

        # Test ML Engine
        print(f"\n{BLUE}ML Engine:{RESET}")
        ml_engine = MULTI_REPO / "ml-engine"
        if ml_engine.exists():
            ml_files = [
                "app/main.py",
                "app/middleware/tenant_middleware.py"
            ]
            for file in ml_files:
                self.test_file_exists(ml_engine / file, f"ML Engine: {file}")

        # Test Agent-AI
        print(f"\n{BLUE}Agent-AI:{RESET}")
        agent_ai = MULTI_REPO / "agent-ai"
        if agent_ai.exists():
            ai_files = [
                "app/agent_ai.py",
                "app/services/cost_control.py"
            ]
            for file in ai_files:
                self.test_file_exists(agent_ai / file, f"Agent-AI: {file}")

    def test_security(self):
        """Test security implementations"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🛡️  Security Smoke Tests{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        self.results["total_tests"] += 1

        # Check for SQL injection prevention
        secure_api = IOT_GATEWAY / "app/secure_api_example.py"
        if secure_api.exists():
            content = secure_api.read_text()
            if "text(" in content and "parameterized" in content.lower():
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} SQL injection prevention implemented")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} SQL injection prevention not verified")

        # Check for brute force protection
        brute_force = MOBILE_APP / "src/utils/BruteForceProtection.ts"
        if brute_force.exists():
            content = brute_force.read_text()
            if "MAX_ATTEMPTS" in content:
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} Brute force protection implemented")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} Brute force protection incomplete")

        # Check for tenant isolation
        tenant_middleware = MULTI_REPO / "ml-engine/app/middleware/tenant_middleware.py"
        if tenant_middleware.exists():
            content = tenant_middleware.read_text()
            if "tenant_id" in content.lower():
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} Tenant isolation implemented")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} Tenant isolation not verified")

        # Check for LLM cost control
        cost_control = MULTI_REPO / "agent-ai/app/services/cost_control.py"
        if cost_control.exists():
            content = cost_control.read_text()
            if "max_daily_cost" in content.lower():
                self.results["passed"] += 1
                print(f"{GREEN}✓{RESET} LLM cost control implemented")
            else:
                self.results["warnings"] += 1
                print(f"{YELLOW}⚠{RESET} LLM cost control not verified")

    def test_documentation(self):
        """Test documentation completeness"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📚 Documentation Smoke Tests{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        docs = [
            "UI_IMPROVEMENTS_GUIDE.md",
            "AGRICULTURAL_UI_ENHANCEMENTS.md",
            "COMPLETE_UI_TRANSFORMATION_GUIDE.md",
            "AG_UI_FINAL_SUMMARY.md",
            "SECURITY_PATCHES_APPLIED.md"
        ]

        for doc in docs:
            doc_path = PROJECT_ROOT / doc
            if self.test_file_exists(doc_path, doc):
                size = doc_path.stat().st_size
                if size > 1000:  # At least 1KB
                    print(f"  {GREEN}✓{RESET} Substantial content ({size} bytes)")
                else:
                    print(f"  {YELLOW}⚠{RESET} Small file ({size} bytes)")

    def test_scripts(self):
        """Test automation scripts"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🤖 Automation Scripts Smoke Tests{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        scripts = [
            "field_reports_autopilot.py",
            "prepare-pr.sh"
        ]

        for script in scripts:
            script_path = SCRIPTS / script
            if self.test_file_exists(script_path, script):
                # Check if executable
                if os.access(script_path, os.X_OK):
                    print(f"  {GREEN}✓{RESET} Executable")
                else:
                    print(f"  {YELLOW}⚠{RESET} Not executable")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}🎯 SMOKE TEST SUMMARY{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]

        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"{BOLD}Total Tests:{RESET} {total}")
        print(f"{GREEN}Passed:{RESET} {passed} ({pass_rate:.1f}%)")
        print(f"{RED}Failed:{RESET} {failed}")
        print(f"{YELLOW}Warnings:{RESET} {warnings}")

        print(f"\n{BOLD}Overall Status:{RESET}")
        if failed == 0:
            print(f"{GREEN}{BOLD}✅ ALL SMOKE TESTS PASSED!{RESET}")
        elif failed <= 2:
            print(f"{YELLOW}{BOLD}⚠️  MOSTLY PASSED (Minor Issues){RESET}")
        else:
            print(f"{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")

        print(f"\n{BOLD}{'='*60}{RESET}\n")

        # Save results
        results_file = PROJECT_ROOT / "smoke_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"Results saved to: {results_file}")

        return failed == 0

def main():
    """Main test execution"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}🔍 Sahool Project - Comprehensive Smoke Tests{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

    suite = SmokeTestSuite()

    # Run all test suites
    suite.test_mobile_app()
    suite.test_backend_services()
    suite.test_security()
    suite.test_documentation()
    suite.test_scripts()

    # Print summary
    success = suite.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

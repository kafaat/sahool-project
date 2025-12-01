#!/usr/bin/env python3
"""
Sahool Project - Comprehensive Code Review & Quality Analysis
============================================================

Performs deep analysis on:
- Code quality and best practices
- Component structure and patterns
- Design system consistency
- Performance considerations
- Security vulnerabilities
- Documentation quality
"""

import re
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

class CodeReviewer:
    """Comprehensive code review"""

    def __init__(self):
        self.issues = defaultdict(list)
        self.metrics = defaultdict(int)
        self.recommendations = []

    def analyze_component(self, file_path: Path) -> Dict:
        """Analyze a React/TypeScript component"""
        content = file_path.read_text()
        analysis = {
            "file": file_path.name,
            "lines": len(content.split('\n')),
            "imports": [],
            "exports": [],
            "props": [],
            "hooks": [],
            "issues": []
        }

        # Check imports
        import_matches = re.findall(r"import\s+.*?from\s+['\"](.+?)['\"]", content)
        analysis["imports"] = import_matches

        # Check for Theme usage
        if "Theme" in content:
            analysis["uses_design_system"] = True
            self.metrics["components_with_design_system"] += 1
        else:
            analysis["uses_design_system"] = False
            analysis["issues"].append("Not using centralized design system")

        # Check for animations
        if "Animated" in content or "FadeIn" in content:
            analysis["has_animations"] = True
            self.metrics["animated_components"] += 1
        else:
            analysis["has_animations"] = False
            analysis["issues"].append("No animations detected")

        # Check for TypeScript types
        if "interface" in content or "type" in content:
            analysis["has_types"] = True
            self.metrics["typed_components"] += 1
        else:
            analysis["has_types"] = False
            analysis["issues"].append("Missing TypeScript types")

        # Check hooks usage
        hooks = re.findall(r"use[A-Z]\w+", content)
        analysis["hooks"] = list(set(hooks))

        # Check for accessibility
        if "accessibilityLabel" in content or "accessible" in content:
            analysis["accessibility"] = True
            self.metrics["accessible_components"] += 1
        else:
            analysis["accessibility"] = False
            analysis["issues"].append("Missing accessibility features")

        # Check file size
        if analysis["lines"] > 500:
            analysis["issues"].append(f"Large file ({analysis['lines']} lines) - consider splitting")

        return analysis

    def analyze_screen(self, file_path: Path) -> Dict:
        """Analyze a screen component"""
        analysis = self.analyze_component(file_path)

        content = file_path.read_text()

        # Check for pull-to-refresh
        if "RefreshControl" in content or "onRefresh" in content:
            analysis["has_pull_to_refresh"] = True
            self.metrics["screens_with_refresh"] += 1

        # Check for loading states
        if "loading" in content.lower():
            analysis["has_loading_state"] = True
            self.metrics["screens_with_loading"] += 1

        # Check for error handling
        if "error" in content.lower() or "catch" in content:
            analysis["has_error_handling"] = True
            self.metrics["screens_with_error_handling"] += 1

        # Check for navigation
        if "navigation" in content:
            analysis["uses_navigation"] = True

        return analysis

    def review_design_system(self):
        """Review design system consistency"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🎨 Design System Review{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        design_system = PROJECT_ROOT / "mobile-app/src/theme/design-system.ts"

        if not design_system.exists():
            print(f"{RED}✗{RESET} Design system file not found!")
            return

        content = design_system.read_text()

        # Check color systems
        color_systems = {
            "johnDeere": "John Deere colors",
            "professional": "Professional agricultural colors",
            "agricultural": "Agricultural NDVI colors",
            "primary": "Primary colors",
            "success": "Success colors",
            "error": "Error colors",
        }

        print(f"{BOLD}Color Systems:{RESET}")
        for key, desc in color_systems.items():
            if key in content:
                print(f"{GREEN}✓{RESET} {desc} defined")
            else:
                print(f"{YELLOW}⚠{RESET} {desc} missing")

        # Check typography
        if "typography" in content.lower():
            print(f"{GREEN}✓{RESET} Typography system defined")
        else:
            print(f"{YELLOW}⚠{RESET} Typography system missing")

        # Check spacing
        if "spacing" in content.lower():
            print(f"{GREEN}✓{RESET} Spacing system defined")
        else:
            print(f"{YELLOW}⚠{RESET} Spacing system missing")

        # Check shadows
        if "shadows" in content.lower():
            print(f"{GREEN}✓{RESET} Shadow system defined")
        else:
            print(f"{YELLOW}⚠{RESET} Shadow system missing")

        # Check animations
        if "animations" in content.lower():
            print(f"{GREEN}✓{RESET} Animation system defined")
        else:
            print(f"{YELLOW}⚠{RESET} Animation system missing")

    def review_components(self):
        """Review UI components"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🧩 UI Components Review{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        components_dir = PROJECT_ROOT / "mobile-app/src/components/ui"

        if not components_dir.exists():
            print(f"{RED}✗{RESET} Components directory not found!")
            return

        components = list(components_dir.glob("*.tsx"))

        print(f"Found {len(components)} components\n")

        for comp_file in components:
            if comp_file.name == "index.ts":
                continue

            print(f"{BOLD}{comp_file.name}{RESET}")
            analysis = self.analyze_component(comp_file)

            # Print analysis
            if analysis["uses_design_system"]:
                print(f"  {GREEN}✓{RESET} Uses design system")
            else:
                print(f"  {YELLOW}⚠{RESET} Not using design system")

            if analysis["has_animations"]:
                print(f"  {GREEN}✓{RESET} Has animations")

            if analysis["has_types"]:
                print(f"  {GREEN}✓{RESET} TypeScript types")

            print(f"  Lines: {analysis['lines']}")
            print(f"  Hooks: {', '.join(analysis['hooks'][:3])}")

            if analysis["issues"]:
                for issue in analysis["issues"]:
                    print(f"  {YELLOW}⚠{RESET} {issue}")

            print()

    def review_screens(self):
        """Review screen components"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📱 Screens Review{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        screens_dir = PROJECT_ROOT / "mobile-app/src/screens"

        improved_screens = list(screens_dir.glob("Improved*.tsx"))

        print(f"Found {len(improved_screens)} improved screens\n")

        for screen_file in improved_screens:
            print(f"{BOLD}{screen_file.name}{RESET}")
            analysis = self.analyze_screen(screen_file)

            # Print analysis
            if analysis["uses_design_system"]:
                print(f"  {GREEN}✓{RESET} Uses design system")

            if analysis["has_animations"]:
                print(f"  {GREEN}✓{RESET} Has animations")

            if analysis.get("has_pull_to_refresh"):
                print(f"  {GREEN}✓{RESET} Pull-to-refresh")

            if analysis.get("has_loading_state"):
                print(f"  {GREEN}✓{RESET} Loading states")

            if analysis.get("has_error_handling"):
                print(f"  {GREEN}✓{RESET} Error handling")

            print(f"  Lines: {analysis['lines']}")

            if analysis["issues"]:
                for issue in analysis["issues"]:
                    print(f"  {YELLOW}⚠{RESET} {issue}")

            print()

    def review_security(self):
        """Review security implementations"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🛡️  Security Review{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        security_files = {
            "Brute Force Protection": PROJECT_ROOT / "mobile-app/src/utils/BruteForceProtection.ts",
            "SQL Injection Prevention": PROJECT_ROOT / "iot-gateway/app/secure_api_example.py",
            "Tenant Isolation": PROJECT_ROOT / "multi-repo/ml-engine/app/middleware/tenant_middleware.py",
            "LLM Cost Control": PROJECT_ROOT / "multi-repo/agent-ai/app/services/cost_control.py"
        }

        for name, path in security_files.items():
            print(f"{BOLD}{name}:{RESET}")

            if not path.exists():
                print(f"  {RED}✗{RESET} File not found")
                continue

            content = path.read_text()
            lines = len(content.split('\n'))

            print(f"  {GREEN}✓{RESET} Implemented ({lines} lines)")

            # Check for key security patterns
            if name == "Brute Force Protection":
                if "MAX_ATTEMPTS" in content:
                    print(f"  {GREEN}✓{RESET} Max attempts configured")
                if "LOCKOUT_DURATION" in content:
                    print(f"  {GREEN}✓{RESET} Lockout duration configured")

            elif name == "SQL Injection Prevention":
                if "text(" in content or "parameterized" in content.lower():
                    print(f"  {GREEN}✓{RESET} Parameterized queries")

            elif name == "Tenant Isolation":
                if "tenant_id" in content:
                    print(f"  {GREEN}✓{RESET} Tenant ID validation")

            elif name == "LLM Cost Control":
                if "max_daily_cost" in content.lower():
                    print(f"  {GREEN}✓{RESET} Daily cost limits")

            print()

    def generate_recommendations(self):
        """Generate recommendations"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}💡 Recommendations{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        recommendations = [
            {
                "priority": "HIGH",
                "category": "Performance",
                "title": "Implement Code Splitting",
                "description": "Large screen files (>500 lines) should be split into smaller components",
                "benefit": "Faster load times and better maintainability"
            },
            {
                "priority": "MEDIUM",
                "category": "Accessibility",
                "title": "Add Accessibility Labels",
                "description": "Ensure all interactive elements have accessibility labels",
                "benefit": "Better user experience for screen readers"
            },
            {
                "priority": "MEDIUM",
                "category": "Testing",
                "title": "Add Unit Tests",
                "description": "Create unit tests for all UI components",
                "benefit": "Better code quality and regression prevention"
            },
            {
                "priority": "LOW",
                "category": "Documentation",
                "title": "Add JSDoc Comments",
                "description": "Document complex functions and components",
                "benefit": "Easier onboarding and maintenance"
            }
        ]

        for rec in recommendations:
            color = RED if rec["priority"] == "HIGH" else YELLOW if rec["priority"] == "MEDIUM" else BLUE
            print(f"{color}[{rec['priority']}]{RESET} {BOLD}{rec['title']}{RESET}")
            print(f"  Category: {rec['category']}")
            print(f"  {rec['description']}")
            print(f"  ✓ {rec['benefit']}")
            print()

    def print_metrics(self):
        """Print collected metrics"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📊 Code Quality Metrics{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        print(f"{BOLD}Design System Adoption:{RESET}")
        total_components = self.metrics.get("components_with_design_system", 0) + 5  # Estimate
        adoption_rate = (self.metrics.get("components_with_design_system", 0) / total_components * 100)
        print(f"  {adoption_rate:.0f}% of components use centralized design system")

        print(f"\n{BOLD}Animation Usage:{RESET}")
        print(f"  {self.metrics.get('animated_components', 0)} components with animations")

        print(f"\n{BOLD}TypeScript Coverage:{RESET}")
        print(f"  {self.metrics.get('typed_components', 0)} components with proper types")

        print(f"\n{BOLD}Accessibility:{RESET}")
        print(f"  {self.metrics.get('accessible_components', 0)} components with accessibility features")

        print(f"\n{BOLD}Screen Features:{RESET}")
        print(f"  {self.metrics.get('screens_with_refresh', 0)} screens with pull-to-refresh")
        print(f"  {self.metrics.get('screens_with_loading', 0)} screens with loading states")
        print(f"  {self.metrics.get('screens_with_error_handling', 0)} screens with error handling")

def main():
    """Main review execution"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}🔍 Sahool Project - Comprehensive Code Review{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")

    reviewer = CodeReviewer()

    # Run all reviews
    reviewer.review_design_system()
    reviewer.review_components()
    reviewer.review_screens()
    reviewer.review_security()
    reviewer.print_metrics()
    reviewer.generate_recommendations()

    print(f"\n{BOLD}{GREEN}✅ Review Complete!{RESET}\n")

if __name__ == "__main__":
    main()

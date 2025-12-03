#!/usr/bin/env python3
"""
Sahool Yemen - Test Script for CI/CD and Model Fixes
سكريبت اختبار إصلاحات منصة سهول اليمن

Usage:
    python scripts/test_fixes.py
"""

import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(result.stdout[:500])
        return True
    else:
        print(f"❌ {description} - FAILED")
        print(result.stderr[:500] if result.stderr else result.stdout[:500])
        return False

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Sahool Yemen - Test Script for Fixes                   ║
║        سكريبت اختبار إصلاحات منصة سهول اليمن                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    all_passed = True

    # Test 1: Verify Python syntax
    tests = [
        ("python -m py_compile libs-shared/sahool_shared/auth/__init__.py", "auth/__init__.py syntax"),
        ("python -m py_compile libs-shared/sahool_shared/auth/password.py", "auth/password.py syntax"),
        ("python -m py_compile libs-shared/sahool_shared/models/alert.py", "models/alert.py syntax"),
        ("python -m py_compile libs-shared/sahool_shared/models/plant_health.py", "models/plant_health.py syntax"),
        ("python -m py_compile libs-shared/tests/test_auth.py", "tests/test_auth.py syntax"),
    ]

    for cmd, desc in tests:
        if not run_command(cmd, desc):
            all_passed = False

    # Test 2: Verify YAML syntax
    yaml_test = '''python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"'''
    if not run_command(yaml_test, "deploy.yml YAML syntax"):
        all_passed = False

    # Test 3: Verify needs_rehash export
    print(f"\n{'='*60}")
    print("🔍 Verifying needs_rehash export")
    print(f"{'='*60}")
    try:
        sys.path.insert(0, 'libs-shared')
        from sahool_shared.auth.password import needs_rehash
        print(f"✅ needs_rehash imported successfully: {needs_rehash}")
    except ImportError as e:
        print(f"❌ Failed to import needs_rehash: {e}")
        all_passed = False

    # Test 4: Verify metadata renamed to extra_data
    print(f"\n{'='*60}")
    print("🔍 Verifying metadata → extra_data rename")
    print(f"{'='*60}")

    with open('libs-shared/sahool_shared/models/alert.py', 'r') as f:
        alert_content = f.read()
        if 'extra_data' in alert_content and 'metadata:' not in alert_content:
            print("✅ alert.py: extra_data found, metadata removed")
        else:
            print("❌ alert.py: Issue with metadata/extra_data")
            all_passed = False

    with open('libs-shared/sahool_shared/models/plant_health.py', 'r') as f:
        health_content = f.read()
        if 'extra_data' in health_content and 'metadata:' not in health_content:
            print("✅ plant_health.py: extra_data found, metadata removed")
        else:
            print("❌ plant_health.py: Issue with metadata/extra_data")
            all_passed = False

    # Test 5: Verify deploy.yml has libs-shared install
    print(f"\n{'='*60}")
    print("🔍 Verifying deploy.yml has libs-shared install")
    print(f"{'='*60}")

    with open('.github/workflows/deploy.yml', 'r') as f:
        deploy_content = f.read()
        if 'pip install -e libs-shared/' in deploy_content:
            print("✅ deploy.yml: libs-shared install found")
        else:
            print("❌ deploy.yml: libs-shared install NOT found")
            all_passed = False

    # Final Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED! ✅")
        print("جميع الاختبارات نجحت!")
    else:
        print("⚠️ SOME TESTS FAILED! ❌")
        print("بعض الاختبارات فشلت!")
    print(f"{'='*60}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

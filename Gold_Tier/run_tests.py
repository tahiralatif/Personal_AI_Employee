#!/usr/bin/env python
"""
Test runner for Gold Tier Phase 1 & 2.

Runs all tests and generates coverage report.

Usage:
    python run_tests.py
    
With coverage:
    python run_tests.py --coverage
"""
import sys
import os
import subprocess
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def run_tests():
    """Run all tests with pytest."""
    print("=" * 60)
    print("Gold Tier Phase 1 & 2 - Test Suite")
    print("=" * 60)
    
    # Test files
    test_files = [
        "tests/test_error_recovery.py",
        "tests/test_audit_logger.py",
        "tests/test_vault_orchestrator.py",
        "tests/test_odoo_integration.py"
    ]
    
    # Check if test files exist
    missing_tests = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_tests.append(test_file)
    
    if missing_tests:
        print(f"\n⚠️  Warning: Missing test files:")
        for test in missing_tests:
            print(f"   - {test}")
        print()
    
    # Run pytest
    print("\n📋 Running tests...\n")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        f"--cov=src/ai_employee_gold",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    result = subprocess.run(cmd)
    
    print("\n" + "=" * 60)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("\n📊 Coverage report generated: htmlcov/index.html")
    else:
        print("❌ Some tests failed")
    
    print("=" * 60)
    
    return result.returncode


def main():
    """Main entry point."""
    print("\n🚀 Gold Tier Test Runner\n")
    
    # Check if in correct directory
    if not Path("tests").exists():
        print("❌ Error: Please run from Gold_Tier directory")
        sys.exit(1)
    
    # Run tests
    exit_code = run_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

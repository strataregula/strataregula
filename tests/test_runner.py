"""
Test runner script for Transfer/Copy subsystem

Provides convenience functions for running different test suites.
"""

import pytest
import sys
from pathlib import Path


def run_unit_tests():
    """Run unit tests only"""
    return pytest.main([
        "tests/transfer/",
        "-m", "not integration",
        "-v"
    ])


def run_integration_tests():
    """Run integration tests only"""
    return pytest.main([
        "tests/test_integration.py",
        "-v"
    ])


def run_transfer_tests():
    """Run all Transfer/Copy subsystem tests"""
    return pytest.main([
        "tests/transfer/",
        "tests/test_integration.py", 
        "-v"
    ])


def run_all_tests():
    """Run complete test suite"""
    return pytest.main([
        "tests/",
        "-v"
    ])


def run_fast_tests():
    """Run fast tests only (exclude slow markers)"""
    return pytest.main([
        "tests/",
        "-m", "not slow",
        "-v"
    ])


def run_coverage():
    """Run tests with coverage report"""
    return pytest.main([
        "tests/",
        "--cov=strataregula",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <command>")
        print("Commands:")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests only") 
        print("  transfer    - Run Transfer/Copy tests only")
        print("  all         - Run all tests")
        print("  fast        - Run fast tests only")
        print("  coverage    - Run tests with coverage")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "unit":
        exit_code = run_unit_tests()
    elif command == "integration":
        exit_code = run_integration_tests()
    elif command == "transfer":
        exit_code = run_transfer_tests()
    elif command == "all":
        exit_code = run_all_tests()
    elif command == "fast":
        exit_code = run_fast_tests()
    elif command == "coverage":
        exit_code = run_coverage()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Flaky Test Rehabilitation Tool

Usage: python tools/rehab_flaky.py

This tool:
1. Loads quarantined tests from tests/flaky_quarantine.yaml
2. Runs each test 10 times consecutively
3. If all 10 runs pass, removes the test from quarantine
4. Updates the quarantine file with results
5. Reports rehabilitated tests for CI automation
"""

import subprocess
import pathlib
import yaml
import sys
import os

REHAB_RUNS = int(os.getenv("REHAB_RUNS", "10"))

def load_quarantine():
    """Load current quarantine list."""
    qfile = pathlib.Path("tests/flaky_quarantine.yaml")
    if not qfile.exists():
        return {}, qfile
    
    try:
        content = qfile.read_text(encoding="utf-8")
        quarantine = yaml.safe_load(content) or {}
        return quarantine, qfile
    except Exception as e:
        print(f"Warning: Could not load quarantine file: {e}")
        return {}, qfile

def test_stability(nodeid: str, runs: int = REHAB_RUNS) -> bool:
    """Test if a nodeid passes consistently across multiple runs."""
    print(f"Testing {nodeid} for {runs} consecutive runs...")
    
    for i in range(runs):
        result = subprocess.run(
            ["pytest", "-q", "--tb=no", nodeid], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"  Run {i+1}: FAILED")
            return False
        
        print(f"  Run {i+1}: PASSED")
    
    print(f"  All {runs} runs PASSED - candidate for rehabilitation!")
    return True

def main():
    print(f"Flaky Test Rehabilitation - Testing with {REHAB_RUNS} consecutive runs")
    print("=" * 60)
    
    quarantine, qfile = load_quarantine()
    
    if not quarantine:
        print("No tests in quarantine - nothing to rehabilitate")
        return 0
    
    print(f"Found {len(quarantine)} quarantined tests")
    
    # Test each quarantined item for stability
    stable_tests = []
    for nodeid, reason in quarantine.items():
        print(f"\nTesting: {nodeid}")
        print(f"Reason: {reason}")
        
        if test_stability(nodeid):
            stable_tests.append(nodeid)
        else:
            print(f"Still flaky - keeping in quarantine")
    
    # Update quarantine file
    if stable_tests:
        print(f"\n🎉 Rehabilitating {len(stable_tests)} stable tests:")
        for nodeid in stable_tests:
            print(f"  - {nodeid}")
            quarantine.pop(nodeid, None)
        
        # Write updated quarantine file
        updated_content = yaml.safe_dump(
            quarantine, 
            sort_keys=True, 
            allow_unicode=True,
            default_flow_style=False
        )
        qfile.write_text(updated_content, encoding="utf-8")
        
        print(f"\nUpdated quarantine file: {qfile}")
        print("These tests are now back in active testing!")
        
    else:
        print(f"\nNo tests passed {REHAB_RUNS} consecutive runs")
        print("All quarantined tests remain unstable")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
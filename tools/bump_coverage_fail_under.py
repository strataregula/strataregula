#!/usr/bin/env python3
"""
Monthly Coverage Threshold Bumper - Safely increase --cov-fail-under by +5pt

Usage: python tools/bump_coverage_fail_under.py

This tool:
1. Finds current --cov-fail-under setting in pytest.ini or pyproject.toml
2. Runs coverage tests to measure current actual coverage
3. Only bumps threshold +5pt if current coverage supports it
4. Updates the appropriate configuration file
5. Safe operation: won't break existing tests
"""
import re, pathlib, subprocess, sys

CANDIDATE_STEP = 5
ROOT = pathlib.Path(".")
INI = ROOT / "pytest.ini"
PJ = ROOT / "pyproject.toml"

def read_fail_under():
    """Read current fail-under threshold and source location"""
    texts = []
    sources = []
    
    if INI.exists(): 
        texts.append(INI.read_text(encoding="utf-8"))
        sources.append('ini')
    if PJ.exists(): 
        texts.append(PJ.read_text(encoding="utf-8"))
        sources.append('pyproject')
    
    for text, source in zip(texts, sources):
        m = re.search(r'--cov-fail-under=(\d+)', text)
        if m:
            return int(m.group(1)), source
    
    return None, None

def write_fail_under(where: str, new: int):
    """Update fail-under threshold in appropriate config file"""
    if where == 'ini' and INI.exists():
        t = INI.read_text(encoding="utf-8")
        t = re.sub(r'--cov-fail-under=\d+', f'--cov-fail-under={new}', t)
        if '--cov-fail-under' not in t:
            # Fallback: add to addopts if not found
            if 'addopts' in t:
                t = re.sub(r'(addopts\s*=\s*)(.*)', f'\\1\\2 --cov-fail-under={new}', t)
            else:
                t += f'\naddopts = --cov=src --cov-report=term-missing:skip-covered --cov-fail-under={new}\n'
        INI.write_text(t, encoding="utf-8")
        
    elif where == 'pyproject' and PJ.exists():
        # Handle pyproject.toml pytest.ini_options array format
        t = PJ.read_text(encoding="utf-8")
        # Try to replace existing entry
        t = re.sub(r'"--cov-fail-under=\d+"', f'"--cov-fail-under={new}"', t)
        # If not found, add to addopts array
        if '--cov-fail-under' not in t and 'addopts = [' in t:
            t = re.sub(r'(addopts = \[[^\]]*)', f'\\1,\n    "--cov-fail-under={new}"', t)
        PJ.write_text(t, encoding="utf-8")

def current_head_cov_pct():
    """Measure current coverage percentage by running tests"""
    try:
        # Detect src structure
        src_path = "src" if (ROOT / "src").exists() else "."
        cmd = ["pytest", f"--cov={src_path}", "--cov-report=xml", "--cov-report=term-missing:skip-covered"]
        
        print(f"Running coverage measurement: {' '.join(cmd)}")
        subprocess.run(cmd, check=False, capture_output=True)
        
        # Parse coverage.xml
        xml_path = ROOT / "coverage.xml"
        if not xml_path.exists():
            return None
            
        x = xml_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'line-rate="([0-9.]+)"', x)
        return round(float(m.group(1)) * 100, 1) if m else None
        
    except Exception as e:
        print(f"Coverage measurement failed: {e}")
        return None

def main():
    print("Coverage Threshold Bumper - Monthly +5pt Automation")
    print("=" * 55)
    
    # Step 1: Find current threshold
    base, where = read_fail_under()
    if base is None:
        print("No --cov-fail-under found in pytest.ini or pyproject.toml")
        return
    
    print(f"Current threshold: {base}% (from {where})")
    
    # Step 2: Measure current coverage
    pct = current_head_cov_pct()
    if pct is None:
        print("Could not measure current coverage; skipping bump")
        return
    
    print(f"Current coverage: {pct}%")
    
    # Step 3: Calculate target and safety check
    target = base + CANDIDATE_STEP
    if pct < target:
        print(f"Skip bump: current coverage {pct}% < target {target}%")
        print(f"Need +{target - pct:.1f}% coverage improvement before next bump")
        return
    
    # Step 4: Safe to bump - update configuration
    write_fail_under(where, target)
    print(f"Bumped threshold: {base}% -> {target}% (current: {pct}%)")
    print(f"Updated {where} configuration")
    print(f"Next month target: {target + CANDIDATE_STEP}%")

if __name__ == "__main__":
    main()
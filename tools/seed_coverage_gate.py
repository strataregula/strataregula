#!/usr/bin/env python3
"""
Coverage Gate Baseline Seeder - Extract current coverage and set fail-under threshold

Usage: python tools/seed_coverage_gate.py

This tool:
1. Runs pytest with coverage reporting
2. Extracts current coverage percentage from coverage.xml
3. Sets --cov-fail-under in pytest.ini to (current - 2pt) to prevent regression
4. Ensures quality gates protect existing code coverage levels
"""
import re, subprocess, pathlib

ROOT = pathlib.Path(".")
PYTEST_INI = ROOT / "pytest.ini"

def run_cov():
    """Run coverage analysis and generate coverage.xml"""
    # Detect src structure
    src_path = "src" if (ROOT / "src").exists() else "."
    cmd = ["pytest", f"--cov={src_path}", "--cov-report=xml", "--cov-report=term-missing:skip-covered"]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)

def read_pct():
    """Extract coverage percentage from coverage.xml"""
    p = ROOT / "coverage.xml"
    if not p.exists():
        return None
    t = p.read_text("utf-8", "ignore")
    m = re.search(r'line-rate="([0-9.]+)"', t)
    return round(float(m.group(1)) * 100, 1) if m else None

def ensure_ini(threshold: int):
    """Update/create pytest.ini with coverage threshold"""
    if not PYTEST_INI.exists():
        PYTEST_INI.write_text("[pytest]\n", encoding="utf-8")
    
    t = PYTEST_INI.read_text(encoding="utf-8")
    
    # Remove existing coverage options to avoid conflicts
    t = re.sub(r'--cov[^\s]*(?:\s*[^\s-][^\s]*)*', '', t)
    
    # Detect src structure for addopts
    src_path = "src" if (ROOT / "src").exists() else "."
    coverage_opts = f"--cov={src_path} --cov-report=term-missing:skip-covered --cov-fail-under={threshold}"
    
    if "addopts" in t:
        # Add to existing addopts line
        t = re.sub(r'(addopts\s*=\s*)(.*)', f'\\1\\2 {coverage_opts}', t)
    else:
        # Add new addopts section
        t += f"\naddopts = {coverage_opts}\n"
    
    PYTEST_INI.write_text(t, encoding="utf-8")

def main():
    print("🧪 Seeding coverage gate from current baseline...")
    
    # Step 1: Run coverage analysis
    run_cov()
    
    # Step 2: Extract current coverage
    pct = read_pct()
    if pct is None:
        print("❌ No coverage.xml generated; skipping seed.")
        return
    
    print(f"📊 Current coverage: {pct}%")
    
    # Step 3: Set threshold with 2pt buffer
    # This prevents immediate regressions while allowing gradual improvement
    base = max(0, int(pct) - 2)
    ensure_ini(base)
    
    print(f"✅ Seeded --cov-fail-under={base} (from {pct}% with 2pt buffer)")
    print(f"📝 Updated pytest.ini with coverage gate")
    print(f"🎯 Quality gate: Current tests will pass, regressions will fail")

if __name__ == "__main__":
    main()
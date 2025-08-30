#!/usr/bin/env python3
"""
Flaky Test Scanner - Detect intermittent test failures

Usage: python tools/flaky_scan.py

This tool:
1. Runs pytest multiple times (default: 3)
2. Collects JUnit XML reports from each run
3. Identifies tests that fail sometimes but not always (flaky)
4. Generates weekly report in docs/reports/flaky.md
5. Helps identify and isolate unstable tests
"""
import subprocess, pathlib, xml.etree.ElementTree as ET, datetime, os, sys

RUNS = int(os.getenv("FLAKY_RUNS", "3"))
REPORT_DIR = pathlib.Path("reports/junit")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def run_once(i: int) -> pathlib.Path:
    """Run pytest once and generate JUnit XML report"""
    xml = REPORT_DIR / f"junit_run_{i}.xml"
    cmd = ["pytest", "-q", f"--junitxml={xml}"]
    print(f"Run {i}: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)
    return xml

def failed_tests(xml_path: pathlib.Path) -> set:
    """Extract failed test names from JUnit XML"""
    failed = set()
    if not xml_path.exists():
        return failed
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for tc in root.iter("testcase"):
            # Check for failure or error elements
            if any(child.tag in ("failure", "error") for child in tc):
                classname = tc.get('classname', '')
                name = tc.get('name', '')
                nodeid = f"{classname}.{name}".strip(".")
                failed.add(nodeid)
    except ET.ParseError as e:
        print(f"Warning: Could not parse {xml_path}: {e}")
    
    return failed

def main():
    print(f"Flaky Test Scanner - Running {RUNS} test iterations")
    print("=" * 55)
    
    # Step 1: Run tests multiple times
    runs = []
    for i in range(1, RUNS + 1):
        xml = run_once(i)
        failed = failed_tests(xml)
        runs.append(failed)
        print(f"Run {i}: {len(failed)} failed tests")
    
    # Step 2: Analyze flaky patterns
    # Tests that failed in at least one run
    union = set().union(*runs)
    # Tests that failed in ALL runs (consistently failing)
    always = set.intersection(*runs) if runs else set()
    # Tests that failed sometimes but not always = flaky
    flaky = union - always
    
    print(f"\nResults: {len(flaky)} flaky, {len(always)} always failing, {len(union)} total failed")
    
    # Step 3: Generate report
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M JST")
    outdir = pathlib.Path("docs/reports")
    outdir.mkdir(parents=True, exist_ok=True)
    outf = outdir / "flaky.md"
    
    lines = [
        f"## Flaky Report – {ts}",
        f"- Runs: {RUNS}",
        f"- Flaky: **{len(flaky)}** | Always failing: {len(always)}",
        "",
        "### Flaky tests"
    ]
    
    if flaky:
        lines.extend([f"- {t}" for t in sorted(flaky)])
    else:
        lines.append("- (none)")
    
    lines.extend(["", "---", ""])
    
    # Prepend to existing report
    prev = outf.read_text(encoding="utf-8") if outf.exists() else ""
    outf.write_text("\n".join(lines) + prev, encoding="utf-8")
    
    print(f"Report written to: {outf}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
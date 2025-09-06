#!/usr/bin/env python3
"""
Rich Run Log Generator for StrataRegula
Generates comprehensive run logs with git diff, test outputs, and CI artifacts
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, timeout=30, capture_output=True):
    """Run command and return (stdout, stderr, returncode)"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out: {cmd}", 1
    except Exception as e:
        return "", f"Command failed: {e}", 1


def get_jst_timestamp():
    """Get current JST timestamp"""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    return now.strftime("%Y%m%d-%H%M")


def get_git_diff_summary():
    """Get git diff summary"""
    stdout, stderr, code = run_cmd("git diff --stat HEAD")
    if code == 0 and stdout.strip():
        return stdout

    # Try staged changes if no working tree changes
    stdout, stderr, code = run_cmd("git diff --stat --cached")
    if code == 0 and stdout.strip():
        return stdout

    return "No changes detected"


def get_git_status():
    """Get git status"""
    stdout, stderr, code = run_cmd("git status --porcelain")
    if code == 0:
        return stdout if stdout.strip() else "Working tree clean"
    return f"Git status failed: {stderr}"


def get_recent_commits():
    """Get recent commits"""
    stdout, stderr, code = run_cmd("git log --oneline -5")
    if code == 0:
        return stdout
    return f"Git log failed: {stderr}"


def run_pytest_quick():
    """Run pytest quick test"""
    stdout, stderr, code = run_cmd("pytest -q", timeout=120)
    return f"Exit code: {code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


def run_pytest_coverage():
    """Run pytest with coverage"""
    stdout, stderr, code = run_cmd("pytest --cov=strataregula --cov-report=term-missing:skip-covered", timeout=180)
    return f"Exit code: {code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


def run_cli_command():
    """Run CLI command"""
    stdout, stderr, code = run_cmd("python -m strataregula --help", timeout=30)
    return f"Exit code: {code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


def run_bench(with_bench=False):
    """Run benchmark if requested"""
    if not with_bench:
        return "Benchmarks skipped (use --with-bench to enable)"

    bench_script = Path("scripts/bench_service_time.py")
    if not bench_script.exists():
        return "Benchmark script not found: scripts/bench_service_time.py"

    stdout, stderr, code = run_cmd("python scripts/bench_service_time.py", timeout=300)
    return f"Exit code: {code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


def get_pr_info():
    """Get PR information using gh CLI"""
    stdout, stderr, code = run_cmd("gh pr view --json title,body,number")
    if code == 0:
        try:
            pr_data = json.loads(stdout)
            return f"PR #{pr_data.get('number', 'N/A')}: {pr_data.get('title', 'N/A')}"
        except:
            pass
    return "Not in PR context or gh CLI unavailable"


def create_run_log(label, summary, intent, with_bench=False, out_dir="docs/run"):
    """Create comprehensive run log"""

    if not summary:
        print("ERROR: --summary is required")
        sys.exit(1)

    # Ensure output directory exists
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = get_jst_timestamp()
    if label:
        filename = f"{timestamp}-JST-{label}.md"
    else:
        filename = f"{timestamp}-JST.md"

    filepath = Path(out_dir) / filename

    # Gather information
    print("DEBUG: Gathering run information...")
    git_diff = get_git_diff_summary()
    git_status = get_git_status()
    recent_commits = get_recent_commits()
    pr_info = get_pr_info()

    print("DEBUG: Running tests...")
    pytest_quick = run_pytest_quick()

    print("DEBUG: Running coverage...")
    pytest_coverage = run_pytest_coverage()

    print("DEBUG: Testing CLI...")
    cli_output = run_cli_command()

    print("DEBUG: Running benchmarks..." if with_bench else "DEBUG: Skipping benchmarks...")
    bench_output = run_bench(with_bench)

    # Generate run log content
    content = f"""# Run Log - {label or 'session'}
- When: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%dT%H-%M')}JST
- Repo: strataregula
- Summary: {summary}

## Intent
{intent or 'Development session'}

## PR Context
{pr_info}

## Git Status
```
{git_status}
```

## Recent Commits
```
{recent_commits}
```

## Git Diff Summary
```
{git_diff}
```

## Commands & Results

### Quick Tests
```
{pytest_quick}
```

### Coverage Tests
```
{pytest_coverage}
```

### CLI Verification
```
{cli_output}
```

### Benchmarks
```
{bench_output}
```

## Key Outputs
- Run log: `{filepath}`
- Test status: {'✅ Available' if 'pytest' in pytest_quick else '❌ Not available'}
- Coverage: {'✅ Available' if '--cov' in pytest_coverage else '❌ Not available'}
- CLI: {'✅ Working' if '--help' in cli_output else '❌ Issues detected'}
- Benchmarks: {'✅ Executed' if with_bench else '⏭️ Skipped'}

## Artifacts
- This run log: `{filepath}`
- Git changes: See diff summary above
- Test outputs: Captured in Commands & Results section

## Next Actions
- Review test results and coverage
- Check for any failing tests or CLI issues
- Ensure all changes are committed appropriately
- Update documentation if needed

---
*Generated: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')}*
"""

    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"SUCCESS: Run log created: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Generate rich run log for StrataRegula")
    parser.add_argument("--label", help="Label for the run log filename")
    parser.add_argument("--summary", required=True, help="Summary of what was accomplished")
    parser.add_argument("--intent", help="Intent/purpose of the session")
    parser.add_argument("--with-bench", action="store_true", help="Include benchmark results")
    parser.add_argument("--out-dir", default="docs/run", help="Output directory")

    args = parser.parse_args()

    filepath = create_run_log(
        label=args.label,
        summary=args.summary,
        intent=args.intent,
        with_bench=args.with_bench,
        out_dir=args.out_dir
    )

    print(f"\nCOMPLETE: Run log ready: {filepath}")


if __name__ == "__main__":
    main()

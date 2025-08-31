#!/usr/bin/env python3
"""
Minimal Run Log writer (JST). Always succeeds even without deps.

Usage:
  python tools/runlog.py --label devcontainer-env-check \
    --summary "DevContainer build & smoke tests" \
    --intent "Ensure unified env works across repos"
  
  python tools/runlog.py --test  # Test Summary format validation
"""
import argparse, os, datetime, pathlib, sys, re

def jst_now():
    from datetime import timezone, timedelta
    return datetime.datetime.now(timezone(timedelta(hours=9)))

def validate_summary_format(content):
    """Test if content matches CI runlog-guard regex"""
    pattern = r'^- +Summary: +[^\s].+'
    return bool(re.search(pattern, content, re.MULTILINE))

def generate_runlog(label, summary, intent, results="", next_actions=""):
    """Generate run log content (testable function)"""
    ts = jst_now().strftime("%Y-%m-%dT%H-%MJST")
    repo = pathlib.Path(".").resolve().name
    
    body = f"""# Run Log - {label}
- When: {ts}
- Repo: {repo}
- Summary: {summary}

## Intent
{intent}

## Commands
(ここに実行コマンドを列挙)

## Results
{results or "(結果の要点を記述)"}

## Next actions
{next_actions or "- 追加対応を記述"}
"""
    return body, ts

def test_mode():
    """Test Summary format validation"""
    test_cases = [
        ("- Summary: Valid content", True),
        ("- Summary:   Valid with spaces", True),
        ("-Summary: No space", False),
        ("- Summary: ", False),  # Empty
        ("- Summary:", False),   # Empty
        ("**Summary**: Wrong format", False),
        ("## Summary", False),
    ]
    
    print("=== Testing Summary format validation ===")
    all_passed = True
    
    for content, expected in test_cases:
        result = validate_summary_format(content)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{content}' -> {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true", help="Run Summary format tests")
    p.add_argument("--label")
    p.add_argument("--summary")
    p.add_argument("--intent")
    p.add_argument("--results", default="")
    p.add_argument("--next", dest="next_actions", default="")
    args = p.parse_args()

    if args.test:
        return test_mode()

    # Require fields for normal operation
    if not all([args.label, args.summary, args.intent]):
        p.error("--label, --summary, and --intent are required (unless using --test)")

    # Generate and validate
    body, ts = generate_runlog(args.label, args.summary, args.intent, args.results, args.next_actions)
    
    if not validate_summary_format(body):
        print("ERROR: Generated content fails Summary format validation", file=sys.stderr)
        return 1
    
    # Write file
    outdir = pathlib.Path("docs/run")
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{ts}-{args.label}.md"
    path.write_text(body, encoding="utf-8")
    
    print(str(path))
    return 0

if __name__ == "__main__":
    sys.exit(main())

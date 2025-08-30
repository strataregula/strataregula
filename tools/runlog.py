#!/usr/bin/env python3
"""
Minimal Run Log writer (JST). Always succeeds even without deps.

Usage:
  python tools/runlog.py --label devcontainer-env-check \
    --summary "DevContainer build & smoke tests" \
    --intent "Ensure unified env works across repos"
"""
import argparse, os, datetime, pathlib, sys

def jst_now():
    from datetime import timezone, timedelta
    return datetime.datetime.now(timezone(timedelta(hours=9)))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--label", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--intent", required=True)
    p.add_argument("--results", default="")
    p.add_argument("--next", dest="next_actions", default="")
    args = p.parse_args()

    ts = jst_now().strftime("%Y-%m-%dT%H-%MJST")
    repo = pathlib.Path(".").resolve().name
    outdir = pathlib.Path("docs/run")
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{ts}-{args.label}.md"

    body = f"""# Run Log - {args.label}
- When: {ts}
- Repo: {repo}
- Summary: {args.summary}

## Intent
{args.intent}

## Commands
(ここに実行コマンドを列挙)

## Results
{args.results or "(結果の要点を記述)"}

## Next actions
{args.next_actions or "- 追加対応を記述"}
"""
    path.write_text(body, encoding="utf-8")
    print(str(path))

if __name__ == "__main__":
    sys.exit(main())

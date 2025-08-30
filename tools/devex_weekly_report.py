#!/usr/bin/env python3
"""
Weekly Health Check Auto-Summary Generator

Scans docs/run/*.md files from the last 7 days, categorizes by Change Class,
and generates a weekly summary report for repository health monitoring.

Usage:
  python tools/devex_weekly_report.py

Output: docs/reports/weekly.md (appends to existing content)
"""
import pathlib
import re
import time
import datetime

JST = datetime.timezone(datetime.timedelta(hours=9))

def load_logs(root: pathlib.Path, since_ts: float):
    """Load all run logs modified within the specified time window."""
    logs = []
    run_dir = root / "docs" / "run"
    
    if not run_dir.exists():
        return logs
        
    for p in sorted(run_dir.glob("*.md")):
        try:
            mtime = p.stat().st_mtime
            if mtime >= since_ts:
                logs.append((mtime, p))
        except FileNotFoundError:
            continue
    return sorted(logs, key=lambda x: x[0], reverse=True)

def parse_log(p: pathlib.Path):
    """Parse a run log file to extract key metadata."""
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except (FileNotFoundError, PermissionError):
        return {
            "file": str(p),
            "summary": "(file read error)",
            "change_class": "C",
            "when": "",
            "label": p.stem,
        }
    
    # Extract Summary line
    summary = re.search(r"^- +Summary:\s*(.+)$", t, re.M)
    
    # Extract Change Class (A|B|C) - look for "Change Class" section
    change = re.search(r"^##\s*Change Class.*?(A|B|C)", t, re.I | re.S | re.M)
    
    # Extract When line
    when = re.search(r"^- +When:\s*(.+)$", t, re.M)
    
    # Extract label from filename (remove JST timestamp prefix)
    label = p.stem
    if "-JST-" in label:
        # Format: 2025-08-30T21-31JST-phase4-sustain-measure-kickoff
        parts = label.split("-JST-", 1)
        if len(parts) > 1:
            label = parts[1]
    elif "-" in label:
        # Fallback: take everything after first few date components
        parts = label.split("-", maxsplit=3)
        if len(parts) > 3:
            label = parts[3]
    
    # Try to make path relative, fallback to absolute
    try:
        file_path = str(p.relative_to(pathlib.Path.cwd()))
    except ValueError:
        file_path = str(p)
    
    return {
        "file": file_path,
        "summary": summary.group(1).strip() if summary else "(no Summary)",
        "change_class": change.group(1).upper() if change else "C",
        "when": when.group(1).strip() if when else "(no When)",
        "label": label,
    }

def main():
    """Generate weekly health summary report."""
    repo = pathlib.Path(".").resolve().name
    since = time.time() - 7*24*3600  # last 7 days
    logs = load_logs(pathlib.Path("."), since)
    parsed = [parse_log(p) for _, p in logs]

    # Count by change class
    a = sum(1 for x in parsed if x["change_class"] == "A")
    b = sum(1 for x in parsed if x["change_class"] == "B")
    c = sum(1 for x in parsed if x["change_class"] == "C")
    
    ts = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

    # Ensure output directory exists
    outdir = pathlib.Path("docs/reports")
    outdir.mkdir(parents=True, exist_ok=True)
    outf = outdir / "weekly.md"

    # Build report content
    lines = []
    lines.append(f"## Weekly Health – {ts}")
    lines.append(f"- Repo: **{repo}**")
    lines.append(f"- Run Logs (7d): **{len(parsed)}**  | A={a}  B={b}  C={c}")
    lines.append("")
    lines.append("### Recent Logs (up to 10)")
    
    # Show up to 10 most recent logs
    for x in parsed[:10]:
        lines.append(f"- {x['when']} — `{x['label']}` — {x['summary']} — {x['file']}")
    
    if not parsed:
        lines.append("- (no recent run logs found)")
    
    lines.append("")
    lines.append("> Note: Change Class が無いログは既定で **C** として集計します。")
    lines.append("\n---\n")

    # Read existing content if any
    prev = ""
    if outf.exists():
        try:
            prev = outf.read_text(encoding="utf-8", errors="ignore")
        except (FileNotFoundError, PermissionError):
            prev = ""

    # Write combined content (new report + existing)
    outf.write_text("\n".join(lines) + prev, encoding="utf-8")
    print(str(outf))

if __name__ == "__main__":
    main()
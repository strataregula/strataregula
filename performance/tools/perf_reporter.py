#!/usr/bin/env python3
"""
Performance Reporter - Generate markdown/HTML reports from benchmark results
MVP version for stable release
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import console utilities for CP932 compatibility
from performance.utils.console import init_stdout_utf8, safe_print, supports_emoji

def load_results_dir(results_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON results from directory"""
    results = []
    for json_file in sorted(Path(results_dir).glob("*.json")):
        try:
            with open(json_file, "r") as f:
                results.append(json.load(f))
        except:
            continue
    return results

def generate_markdown_report(results: List[Dict[str, Any]]) -> str:
    """Generate markdown report for PR comments"""
    
    if not results:
        return "No benchmark results found."
    
    # Take latest result
    latest = results[-1]
    metrics = latest.get("metrics", {})
    gate = latest.get("gate", {})
    run_info = latest.get("run", {})
    
    # Build report
    report = []
    report.append("## 📊 Performance Benchmark Report")
    report.append("")
    
    # Summary
    verdict_icon = "✅" if gate.get("verdict") == "PASS" else "❌"
    report.append(f"**Status**: {verdict_icon} {gate.get('verdict', 'UNKNOWN')}")
    report.append(f"**Project**: {run_info.get('project', 'unknown')}")
    report.append(f"**Profile**: {run_info.get('profile', 'unknown')}")
    report.append(f"**Commit**: {run_info.get('git_sha', 'unknown')}")
    report.append("")
    
    # Performance metrics table
    report.append("### Performance Metrics")
    report.append("")
    report.append("| Metric | Value | Threshold | Status |")
    report.append("|--------|-------|-----------|--------|")
    
    # Speedup metrics
    speedup_p50 = metrics.get("speedup_p50", 0)
    speedup_p95 = metrics.get("speedup_p95", 0)
    abs_p95 = metrics.get("absolute_p95_ms", 0)
    
    p50_status = "✅" if speedup_p50 >= gate.get("p50x", 15) else "❌"
    p95_status = "✅" if speedup_p95 >= gate.get("p95x", 12) else "❌"
    abs_status = "✅" if abs_p95 <= gate.get("absolute_ms", 35) else "❌"
    
    report.append(f"| Speedup (p50) | {speedup_p50:.1f}x | ≥{gate.get('p50x', 15)}x | {p50_status} |")
    report.append(f"| Speedup (p95) | {speedup_p95:.1f}x | ≥{gate.get('p95x', 12)}x | {p95_status} |")
    report.append(f"| Absolute p95 | {abs_p95:.1f}ms | ≤{gate.get('absolute_ms', 35)}ms | {abs_status} |")
    report.append("")
    
    # Detailed metrics
    report.append("### Detailed Results")
    report.append("")
    report.append("| Path | p50 (ms) | p95 (ms) | Hits | Rebuilds |")
    report.append("|------|----------|----------|------|----------|")
    
    compiled = metrics.get("compiled", {})
    fallback = metrics.get("fallback", {})
    
    report.append(f"| Compiled | {compiled.get('p50_ms', 0):.2f} | {compiled.get('p95_ms', 0):.2f} | "
                 f"{compiled.get('hits', 0)} | {compiled.get('rebuilds', 0)} |")
    report.append(f"| Fallback | {fallback.get('p50_ms', 0):.2f} | {fallback.get('p95_ms', 0):.2f} | "
                 f"{fallback.get('hits', 0)} | {fallback.get('regex', 0)} |")
    report.append("")
    
    # Historical trend (if multiple results)
    if len(results) > 1:
        report.append("### Historical Trend (Last 5 Runs)")
        report.append("")
        report.append("| Run Time | Speedup p50 | Speedup p95 | Verdict |")
        report.append("|----------|-------------|-------------|---------|")
        
        for result in results[-5:]:
            run_time = result.get("run", {}).get("timestamp", "")[:16]
            m = result.get("metrics", {})
            g = result.get("gate", {})
            verdict_emoji = "✅" if g.get("verdict") == "PASS" else "❌"
            report.append(f"| {run_time} | {m.get('speedup_p50', 0):.1f}x | "
                         f"{m.get('speedup_p95', 0):.1f}x | {verdict_emoji} |")
        report.append("")
    
    # Footer
    report.append("---")
    report.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
    report.append(f"*Headroom: {gate.get('headroom_pct', 0):.1f}%*")
    
    # Add docs links
    docs = latest.get("docs", {})
    if docs:
        report.append("")
        report.append("📚 **Documentation**:")
        for key, path in docs.items():
            if path:
                report.append(f"- [{key.title()}]({path})")
    
    return "\n".join(report)

def main():
    # Initialize UTF-8 output
    init_stdout_utf8()
    
    parser = argparse.ArgumentParser(description="Performance Reporter - Generate reports")
    parser.add_argument("--in", dest="input", default="performance/results", 
                       help="Input directory with JSON results")
    parser.add_argument("--out", help="Output file path (markdown)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"],
                       help="Output format")
    
    args = parser.parse_args()
    
    # Load results
    results = load_results_dir(args.input)
    
    if not results:
        safe_print("❌ No benchmark results found", "No benchmark results found")
        return 1
    
    report_msg = f"📊 Generating report from {len(results)} benchmark results..." if supports_emoji() else f"Generating report from {len(results)} benchmark results..."
    safe_print(report_msg)
    
    # Generate report
    if args.format == "markdown":
        report = generate_markdown_report(results)
    else:
        # HTML format (future enhancement)
        report = f"<pre>{generate_markdown_report(results)}</pre>"
    
    # Output
    if args.out:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        safe_print(f"✅ Report saved to: {args.out}", f"Report saved to: {args.out}")
    else:
        print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
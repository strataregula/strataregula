#!/usr/bin/env python3
"""
Performance Guard - Two-tier gating system for performance regression detection
MVP version for stable release
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import console utilities for CP932 compatibility
from performance.utils.console import init_stdout_utf8, safe_print, supports_emoji

def load_results(input_path: str) -> Dict[str, Any]:
    """Load benchmark results from JSON"""
    if input_path == "-":
        return json.load(sys.stdin)
    
    with open(input_path, "r") as f:
        return json.load(f)

def evaluate_gate(metrics: Dict[str, Any], p50x: float, p95x: float, absolute_ms: float) -> Dict[str, Any]:
    """Evaluate performance against gate criteria"""
    
    speedup_p50 = metrics.get("speedup_p50", 0)
    speedup_p95 = metrics.get("speedup_p95", 0)
    absolute_p95 = metrics.get("absolute_p95_ms", float('inf'))
    
    # Two-tier gate evaluation
    p50_pass = speedup_p50 >= p50x
    p95_pass = speedup_p95 >= p95x
    absolute_pass = absolute_p95 <= absolute_ms
    
    # Overall verdict
    verdict = "PASS" if (p50_pass and p95_pass and absolute_pass) else "FAIL"
    
    # Calculate headroom (minimum percentage above threshold)
    headrooms = []
    if p50x > 0:
        headrooms.append(((speedup_p50 - p50x) / p50x) * 100)
    if p95x > 0:
        headrooms.append(((speedup_p95 - p95x) / p95x) * 100)
    if absolute_ms > 0:
        headrooms.append(((absolute_ms - absolute_p95) / absolute_ms) * 100)
    
    min_headroom = min(headrooms) if headrooms else 0
    
    return {
        "p50x": p50x,
        "p95x": p95x,
        "absolute_ms": absolute_ms,
        "verdict": verdict,
        "headroom_pct": round(min_headroom, 1),
        "details": {
            "p50_pass": p50_pass,
            "p95_pass": p95_pass,
            "absolute_pass": absolute_pass,
            "speedup_p50": round(speedup_p50, 1),
            "speedup_p95": round(speedup_p95, 1),
            "absolute_p95_ms": round(absolute_p95, 1)
        }
    }

def main():
    # Initialize UTF-8 output
    init_stdout_utf8()
    
    parser = argparse.ArgumentParser(description="Performance Guard - Evaluate benchmark results")
    parser.add_argument("--in", dest="input", default="-", help="Input JSON file (- for stdin)")
    parser.add_argument("--p50x", type=float, default=15, help="Minimum p50 speedup multiplier")
    parser.add_argument("--p95x", type=float, default=12, help="Minimum p95 speedup multiplier")
    parser.add_argument("--abs-ms", dest="absolute_ms", type=float, default=35, 
                       help="Maximum absolute p95 in milliseconds")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    # Load results
    try:
        results = load_results(args.input)
    except Exception as e:
        safe_print(f"❌ Failed to load results: {e}", f"Failed to load results: {e}")
        return 1
    
    # Evaluate gate
    metrics = results.get("metrics", {})
    gate_result = evaluate_gate(metrics, args.p50x, args.p95x, args.absolute_ms)
    
    # Update results with gate evaluation
    results["gate"] = gate_result
    
    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        profile = results.get("run", {}).get("profile", "unknown")
        project = results.get("run", {}).get("project", "unknown")
        
        title = "🔍 Performance Guard" if supports_emoji() else "Performance Guard"
        safe_print(f"{title} - {project} ({profile})")
        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "="*38)
        safe_print(f"Speedup p50: {gate_result['details']['speedup_p50']}x (threshold: ≥{args.p50x}x)")
        safe_print(f"Speedup p95: {gate_result['details']['speedup_p95']}x (threshold: ≥{args.p95x}x)")
        safe_print(f"Absolute p95: {gate_result['details']['absolute_p95_ms']}ms (threshold: ≤{args.absolute_ms}ms)")
        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "="*38)
        
        if gate_result["verdict"] == "PASS":
            pass_msg = f"✅ PASS - Headroom: {gate_result['headroom_pct']}%" if supports_emoji() else f"PASS - Headroom: {gate_result['headroom_pct']}%"
            safe_print(pass_msg)
        else:
            fail_msg = f"❌ FAIL - Performance regression detected" if supports_emoji() else "FAIL - Performance regression detected"
            safe_print(fail_msg)
            if not gate_result["details"]["p50_pass"]:
                safe_print("   • p50 speedup below threshold", "   - p50 speedup below threshold")
            if not gate_result["details"]["p95_pass"]:
                safe_print("   • p95 speedup below threshold", "   - p95 speedup below threshold")
            if not gate_result["details"]["absolute_pass"]:
                safe_print("   • Absolute latency exceeds limit", "   - Absolute latency exceeds limit")
    
    # Exit code based on verdict
    return 0 if gate_result["verdict"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
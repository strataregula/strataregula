#!/usr/bin/env python3
"""
StrataRegula Benchmark Integration Script - Seamless CI/CD integration

This script provides a drop-in replacement for existing benchmark commands
while adding comprehensive multi-format output capabilities optimized for StrataRegula.

Usage:
  python scripts/bench_integration.py                    # Run with enhanced output
  python scripts/bench_integration.py --legacy           # Run original benchmark only
  python scripts/bench_integration.py --ci               # Optimize for CI environment
"""

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def safe_print(content: str) -> None:
    """Safely print content with fallback for encoding issues."""
    try:
        print(content)
    except UnicodeEncodeError:
        safe_content = content.encode("ascii", errors="replace").decode("ascii")
        print(safe_content)


def run_original_benchmark(
    output_file: str = "bench_guard.json", additional_args: list[str] | None = None
) -> int:
    """Run the original StrataRegula benchmark script."""
    # Use the root-level bench_guard.py for StrataRegula
    cmd = [sys.executable, "bench_guard.py", "--output", output_file]
    if additional_args:
        cmd.extend(additional_args)

    safe_print(f"Running original StrataRegula benchmark: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, cwd=Path.cwd())
    return result.returncode


def run_enhanced_reporting(
    input_file: str, formats: list[str] | None = None, ci_mode: bool = False
) -> int:
    """Run enhanced reporting on StrataRegula benchmark results."""
    if not Path(input_file).exists():
        safe_print(f"Benchmark results not found: {input_file}")
        return 1

    formats = formats or ["all"]
    cmd = [sys.executable, "scripts/bench_reporter.py", input_file]

    # Add format specification
    if len(formats) == 1:
        cmd.extend(["--format", formats[0]])
    else:
        cmd.extend(["--format", "all"])

    # CI optimizations for StrataRegula
    if ci_mode or os.getenv("GITHUB_ACTIONS") == "true":
        cmd.extend(["--ci-summary", "--auto-ci"])

    safe_print(f"Running enhanced StrataRegula reporting: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, cwd=Path.cwd())
    return result.returncode


def create_artifact_bundle(base_name: str = "bench_guard") -> list[Path]:
    """Bundle all StrataRegula benchmark outputs for CI artifact upload."""
    artifacts = []
    extensions = [".json", ".md", "_console.txt", "_ci_summary.md"]

    for ext in extensions:
        artifact_path = Path(f"{base_name}{ext}")
        if artifact_path.exists():
            artifacts.append(artifact_path)

    # Include run files if they exist (from 3-run evaluation)
    for i in range(1, 4):
        run_file = Path(f"{base_name}_run{i}.json")
        if run_file.exists():
            artifacts.append(run_file)

    return artifacts


def check_benchmark_health(results_file: str) -> dict:
    """Check benchmark health and provide diagnostics."""
    health_report = {
        "config_valid": False,
        "results_parsable": False,
        "thresholds_reasonable": False,
        "performance_inverted": False,
        "recommendations": [],
    }

    try:
        if not Path(results_file).exists():
            health_report["recommendations"].append(
                "Run benchmark first to generate results"
            )
            return health_report

        with open(results_file, encoding="utf-8") as f:
            data = json.load(f)

        health_report["results_parsable"] = True

        # Check configuration sanity
        config = data.get("config", {})
        if config.get("n", 0) > 0 and config.get("min_ratio", 0) > 0:
            health_report["config_valid"] = True

        # Check threshold reasonableness
        min_ratio = config.get("min_ratio", 0)
        max_p95 = config.get("max_p95_us", 0)
        if 1 <= min_ratio <= 1000 and 1 <= max_p95 <= 10000:
            health_report["thresholds_reasonable"] = True

        # Check for performance inversions (slow > fast)
        if "benchmarks" in data:
            for name, bench in data["benchmarks"].items():
                if "fast" in bench and "slow" in bench:
                    fast_ops = bench["fast"].get("ops", 0)
                    slow_ops = bench["slow"].get("ops", 0)
                    if slow_ops > fast_ops * 1.5:  # Significant inversion
                        health_report["performance_inverted"] = True
                        health_report["recommendations"].append(
                            f"Performance inversion in {name}: slow ({slow_ops:.0f}) > fast ({fast_ops:.0f})"
                        )

        # Generate recommendations
        if not health_report["config_valid"]:
            health_report["recommendations"].append(
                "Review benchmark configuration parameters"
            )

        if not health_report["thresholds_reasonable"]:
            health_report["recommendations"].append(
                "Adjust performance thresholds to realistic values"
            )

        if health_report["performance_inverted"]:
            health_report["recommendations"].append(
                "Investigate why 'fast' implementations are slower than 'slow' ones"
            )

        if data.get("passed", False):
            health_report["recommendations"].append(
                "All checks passed - benchmark is healthy"
            )

    except Exception as e:
        health_report["recommendations"].append(f"Health check failed: {e}")

    return health_report


def main() -> int:
    """Main integration script for enhanced StrataRegula benchmark reporting."""
    parser = argparse.ArgumentParser(
        description="StrataRegula Benchmark Integration with Enhanced Reporting"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Run original benchmark only (no enhanced reporting)",
    )
    parser.add_argument("--ci", action="store_true", help="Optimize for CI environment")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "console", "all"],
        default="all",
        help="Enhanced report format(s)",
    )
    parser.add_argument(
        "--output", default="bench_guard.json", help="Primary benchmark output file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without running benchmark",
    )
    parser.add_argument(
        "--list-artifacts",
        action="store_true",
        help="List available benchmark artifacts",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check benchmark health and provide diagnostics",
    )

    args = parser.parse_args()

    try:
        # Handle special commands
        if args.list_artifacts:
            artifacts = create_artifact_bundle(Path(args.output).stem)
            safe_print(
                f"Available StrataRegula benchmark artifacts ({len(artifacts)} files):"
            )
            for artifact in artifacts:
                size_kb = artifact.stat().st_size / 1024 if artifact.exists() else 0
                safe_print(f"   * {artifact} ({size_kb:.1f} KB)")
            return 0

        if args.health_check:
            health = check_benchmark_health(args.output)
            safe_print("StrataRegula Benchmark Health Check:")
            safe_print(
                f"   * Config Valid: {'[OK]' if health['config_valid'] else '[FAIL]'}"
            )
            safe_print(
                f"   * Results Parsable: {'[OK]' if health['results_parsable'] else '[FAIL]'}"
            )
            safe_print(
                f"   * Thresholds Reasonable: {'[OK]' if health['thresholds_reasonable'] else '[FAIL]'}"
            )
            safe_print(
                f"   * Performance Inverted: {'[WARN]' if health['performance_inverted'] else '[OK]'}"
            )

            if health["recommendations"]:
                safe_print("\nRecommendations:")
                for rec in health["recommendations"]:
                    safe_print(f"   * {rec}")

            return 0 if health["config_valid"] and health["results_parsable"] else 1

        safe_print("Starting StrataRegula Integrated Benchmark Suite")
        safe_print(f"Mode: {'Legacy' if args.legacy else 'Enhanced'}")
        safe_print(f"CI Mode: {'Enabled' if args.ci else 'Disabled'}")
        safe_print("=" * 60)

        # Phase 1: Run original benchmark
        benchmark_args = []
        if args.dry_run:
            benchmark_args.append("--dry-run")

        result = run_original_benchmark(args.output, benchmark_args)

        if args.dry_run:
            safe_print("Dry run validation completed")
            return result

        if result != 0:
            safe_print("Original benchmark failed, but continuing with reporting...")

        # Phase 2: Enhanced reporting (unless legacy mode)
        if not args.legacy:
            enhanced_result = run_enhanced_reporting(
                args.output, [args.format], args.ci
            )

            if enhanced_result != 0:
                safe_print(
                    "Enhanced reporting had issues, but original results preserved"
                )

        # Phase 3: Artifact summary for CI
        if args.ci or os.getenv("GITHUB_ACTIONS") == "true":
            artifacts = create_artifact_bundle(Path(args.output).stem)
            safe_print(f"\nStrataRegula CI Artifacts Ready ({len(artifacts)} files):")
            for artifact in artifacts:
                safe_print(f"   * {artifact}")

            # Set GitHub Actions outputs for workflow consumption
            if os.getenv("GITHUB_OUTPUT"):
                with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
                    f.write(
                        f"strataregula_benchmark_passed={'true' if result == 0 else 'false'}\n"
                    )
                    f.write(f"artifacts_count={len(artifacts)}\n")
                    f.write(f"primary_result={args.output}\n")

                    # Include artifacts list for upload action
                    artifact_list = ",".join(str(a) for a in artifacts)
                    f.write(f"artifact_files={artifact_list}\n")

        # Phase 4: Performance health check for CI
        if args.ci and Path(args.output).exists():
            health = check_benchmark_health(args.output)
            if health["performance_inverted"]:
                safe_print("\nPerformance Health Warning:")
                safe_print(
                    "   Detected performance inversions - review benchmark configuration"
                )
                for rec in health["recommendations"]:
                    if "inversion" in rec.lower():
                        safe_print(f"   * {rec}")

        safe_print(f"\nStrataRegula integration complete - exit code: {result}")
        return result

    except Exception as e:
        safe_print(f"StrataRegula integration script failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

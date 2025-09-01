#!/usr/bin/env python3
"""
Enhanced Benchmark Reporter - Multi-format output generator for StrataRegula

Provides triple-layer reporting for benchmark results:
1. JSON: Machine-readable structured data (existing compatibility)
2. Markdown: Human-readable reports for PRs and documentation
3. Console: Interactive terminal output for development

Optimized for StrataRegula benchmark patterns and CI integration.
"""

import io
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Fix Windows console encoding issues
if sys.platform == "win32":
    # Set UTF-8 encoding for stdout to handle emojis
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class OutputFormat(Enum):
    """Supported output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    CONSOLE = "console"
    ALL = "all"


@dataclass
class BenchmarkMetrics:
    """Standardized benchmark metrics across formats."""

    ops_per_sec: float
    p50_us: float
    p95_us: float
    p99_us: float
    min_us: float | None = None
    max_us: float | None = None
    mean_us: float | None = None
    std_us: float | None = None


@dataclass
class ComponentResult:
    """Individual component benchmark result."""

    name: str
    metrics: BenchmarkMetrics
    runs: list[float] | None = None
    median_time_s: float | None = None


@dataclass
class BenchmarkReport:
    """Complete benchmark report structure."""

    timestamp: str
    config: dict[str, Any]
    components: list[ComponentResult]
    comparison: dict[str, Any]
    passed: bool
    error: str | None = None
    diagnostics: dict[str, Any] | None = None


class StrataRegulaReporter:
    """Multi-format benchmark result reporter for StrataRegula."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_json_results(self, json_path: Path) -> BenchmarkReport:
        """Load and normalize StrataRegula JSON benchmark results."""
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        components = []

        # Handle StrataRegula-specific formats
        if "benchmarks" in data:
            # New strataregula format with benchmarks object
            for name, bench_data in data["benchmarks"].items():
                if "fast" in bench_data:
                    fast_metrics = BenchmarkMetrics(
                        ops_per_sec=bench_data["fast"].get("ops", 0),
                        p50_us=bench_data["fast"].get("p50_us", 0),
                        p95_us=bench_data["fast"].get("p95_us", 0),
                        p99_us=bench_data["fast"].get("p99_us", 0),
                        min_us=bench_data["fast"].get("min_us"),
                        max_us=bench_data["fast"].get("max_us"),
                        mean_us=bench_data["fast"].get("mean_us"),
                        std_us=bench_data["fast"].get("std_us"),
                    )
                    components.append(
                        ComponentResult(name=f"{name}_fast", metrics=fast_metrics)
                    )

                if "slow" in bench_data:
                    slow_metrics = BenchmarkMetrics(
                        ops_per_sec=bench_data["slow"].get("ops", 0),
                        p50_us=bench_data["slow"].get("p50_us", 0),
                        p95_us=bench_data["slow"].get("p95_us", 0),
                        p99_us=bench_data["slow"].get("p99_us", 0),
                        min_us=bench_data["slow"].get("min_us"),
                        max_us=bench_data["slow"].get("max_us"),
                        mean_us=bench_data["slow"].get("mean_us"),
                        std_us=bench_data["slow"].get("std_us"),
                    )
                    components.append(
                        ComponentResult(name=f"{name}_slow", metrics=slow_metrics)
                    )

        elif "fast" in data and "slow" in data:
            # Legacy strataregula format
            fast_metrics = BenchmarkMetrics(
                ops_per_sec=data["fast"].get("ops", 0),
                p50_us=data["fast"].get("p50_us", 0),
                p95_us=data["fast"].get("p95_us", 0),
                p99_us=data["fast"].get("p99_us", 0),
                min_us=data["fast"].get("min_us"),
                max_us=data["fast"].get("max_us"),
                mean_us=data["fast"].get("mean_us"),
                std_us=data["fast"].get("std_us"),
            )
            components.append(ComponentResult(name="fast_path", metrics=fast_metrics))

            slow_metrics = BenchmarkMetrics(
                ops_per_sec=data["slow"].get("ops", 0),
                p50_us=data["slow"].get("p50_us", 0),
                p95_us=data["slow"].get("p95_us", 0),
                p99_us=data["slow"].get("p99_us", 0),
                min_us=data["slow"].get("min_us"),
                max_us=data["slow"].get("max_us"),
                mean_us=data["slow"].get("mean_us"),
                std_us=data["slow"].get("std_us"),
            )
            components.append(ComponentResult(name="slow_path", metrics=slow_metrics))

        return BenchmarkReport(
            timestamp=data.get("timestamp", ""),
            config=data.get("config", {}),
            components=components,
            comparison=data.get("comparison", {}),
            passed=data.get("passed", False),
            error=data.get("error"),
            diagnostics=data.get("diagnostics"),
        )

    def _safe_print(self, content: str) -> None:
        """Safely print content with fallback for encoding issues."""
        try:
            print(content)
        except UnicodeEncodeError:
            # Fallback: replace problematic characters with ASCII equivalents
            safe_content = content.encode("ascii", errors="replace").decode("ascii")
            print(safe_content)

    def generate_console_output(self, report: BenchmarkReport) -> str:
        """Generate enhanced console output with Japanese-style indicators."""
        lines = []

        # Header with status (Windows-safe ASCII)
        status_symbol = "[PASS]" if report.passed else "[FAIL]"
        status_text = "PASSED" if report.passed else "FAILED"
        lines.append("=" * 80)
        lines.append(f"StrataRegula Benchmark Results - {status_symbol} {status_text}")
        lines.append(f"Timestamp: {report.timestamp}")
        lines.append("=" * 80)

        # Configuration summary
        lines.append("\nConfiguration:")
        config = report.config
        lines.append(f"   * Operations: {config.get('n', 0):,}")
        lines.append(f"   * Warmup: {config.get('warmup', 0):,}")
        lines.append(f"   * Min Ratio: >={config.get('min_ratio', 0)}x")
        lines.append(f"   * Max p95: <={config.get('max_p95_us', 0)}us")

        # Component performance table
        lines.append("\nComponent Performance:")
        lines.append(
            f"{'Component':<25} {'Ops/sec':<12} {'p50 (us)':<10} {'p95 (us)':<10} {'Status':<8}"
        )
        lines.append("-" * 75)

        for component in report.components:
            # Clean up component names for display (ASCII safe)
            name = component.name.replace("_fast", " (Fast)").replace(
                "_slow", " (Slow)"
            )
            name = name.replace("pattern_expansion", "Pattern Expansion")
            name = name.replace("config_compilation", "Config Compilation")
            name = name.replace("kernel_cache", "Kernel Cache")
            name = name[:24]  # Truncate for table formatting

            metrics = component.metrics

            # Performance status indicators (ASCII compatible)
            if metrics.p95_us <= 50:
                perf_status = "[FAST]"
            elif metrics.p95_us <= 100:
                perf_status = "[OK]"
            else:
                perf_status = "[SLOW]"

            lines.append(
                f"{name:<25} {metrics.ops_per_sec:>11,.0f} {metrics.p50_us:>9.1f} {metrics.p95_us:>9.1f} {perf_status}"
            )

        # Performance analysis
        if len(report.components) >= 2:
            fastest = max(report.components, key=lambda c: c.metrics.ops_per_sec)
            slowest = min(report.components, key=lambda c: c.metrics.ops_per_sec)
            speed_ratio = fastest.metrics.ops_per_sec / max(
                1, slowest.metrics.ops_per_sec
            )

            lines.append("\nPerformance Analysis:")
            lines.append(
                f"   * Fastest: {fastest.name} ({fastest.metrics.ops_per_sec:,.0f} ops/s)"
            )
            lines.append(
                f"   * Slowest: {slowest.name} ({slowest.metrics.ops_per_sec:,.0f} ops/s)"
            )
            lines.append(f"   * Speed Ratio: {speed_ratio:.1f}x")

        # Failure analysis
        if not report.passed:
            lines.append("\nPerformance Issues Detected:")
            comparison = report.comparison

            if not comparison.get("ratio_ok", True):
                min_ratio = comparison.get("ratio_fast_over_slow", 0)
                required_ratio = config.get("min_ratio", 0)
                lines.append(
                    f"   X Speed ratio {min_ratio:.1f}x < {required_ratio}x (requirement)"
                )

            if not comparison.get("fast_p95_ok", True):
                max_p95 = max((c.metrics.p95_us for c in report.components), default=0)
                threshold = config.get("max_p95_us", 0)
                lines.append(
                    f"   X p95 latency {max_p95:.1f}us > {threshold}us (threshold)"
                )

            lines.append("\nRecommended Actions:")
            lines.append("   * Profile critical paths for bottlenecks")
            lines.append("   * Review recent algorithmic changes")
            lines.append("   * Consider caching or optimization strategies")

        # Diagnostics summary
        if report.diagnostics:
            diag = report.diagnostics
            lines.append("\nEnvironment:")
            lines.append(
                f"   * Python: {diag.get('python_version', 'unknown').split()[0]}"
            )
            lines.append(f"   * Platform: {diag.get('platform', 'unknown')}")
            if "service_patterns" in diag:
                lines.append(
                    f"   * Patterns: {diag['service_patterns']} -> {diag.get('direct_mappings', 0)} mappings"
                )

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_markdown_report(self, report: BenchmarkReport) -> str:
        """Generate detailed Markdown report for StrataRegula PRs."""
        lines = []

        # Header with executive summary
        status_emoji = "✅" if report.passed else "❌"
        status_text = "PASSED" if report.passed else "FAILED"
        lines.append(
            f"# 🏯 StrataRegula Benchmark Report - {status_emoji} {status_text}"
        )
        lines.append(f"\n**実行時刻:** {report.timestamp}")

        # Executive summary
        lines.append("\n## 📋 実行サマリー")
        if report.passed:
            lines.append("✅ すべての性能閾値をクリア。回帰は検出されませんでした。")
        else:
            lines.append("⚠️ **性能回帰を検出** - マージ前に確認が必要です。")

        # Performance metrics table
        lines.append("\n## 📊 性能メトリクス")
        lines.append(
            "| コンポーネント | Ops/sec | p50 (μs) | p95 (μs) | p99 (μs) | 状態 |"
        )
        lines.append(
            "|-------------|---------|----------|----------|----------|------|"
        )

        for component in report.components:
            # Localize component names
            name = component.name
            if "fast" in name:
                display_name = name.replace("_fast", "").replace("_", " ") + " (高速)"
            elif "slow" in name:
                display_name = name.replace("_slow", "").replace("_", " ") + " (低速)"
            else:
                display_name = name.replace("_", " ")

            # Map to Japanese terms
            display_name = display_name.replace("pattern expansion", "パターン展開")
            display_name = display_name.replace("config compilation", "設定コンパイル")
            display_name = display_name.replace("kernel cache", "カーネルキャッシュ")

            m = component.metrics
            status = (
                "🟢 高速"
                if m.p95_us <= 50
                else "🟡 OK"
                if m.p95_us <= 100
                else "🔴 低速"
            )
            lines.append(
                f"| **{display_name}** | {m.ops_per_sec:,.0f} | {m.p50_us:.1f} | {m.p95_us:.1f} | {m.p99_us:.1f} | {status} |"
            )

        # Threshold analysis
        config = report.config
        comparison = report.comparison
        lines.append("\n## 🎯 閾値分析")
        lines.append("| メトリクス | 実測値 | 閾値 | 判定 |")
        lines.append("|-----------|-------|------|------|")

        ratio = comparison.get("ratio_fast_over_slow", 0)
        min_ratio = config.get("min_ratio", 0)
        ratio_status = "✅ 合格" if comparison.get("ratio_ok", False) else "❌ 不合格"
        lines.append(f"| 速度比 | {ratio:.1f}x | ≥{min_ratio}x | {ratio_status} |")

        max_p95 = max((c.metrics.p95_us for c in report.components), default=0)
        p95_threshold = config.get("max_p95_us", 0)
        p95_status = "✅ 合格" if comparison.get("fast_p95_ok", False) else "❌ 不合格"
        lines.append(
            f"| 最大p95レイテンシ | {max_p95:.1f}μs | ≤{p95_threshold}μs | {p95_status} |"
        )

        # Detailed results
        lines.append("\n## 🔬 詳細結果")

        # Group fast/slow pairs for better readability
        components_by_base = {}
        for component in report.components:
            base_name = component.name.replace("_fast", "").replace("_slow", "")
            if base_name not in components_by_base:
                components_by_base[base_name] = {}

            if "_fast" in component.name:
                components_by_base[base_name]["fast"] = component
            elif "_slow" in component.name:
                components_by_base[base_name]["slow"] = component
            else:
                components_by_base[base_name]["single"] = component

        for base_name, variants in components_by_base.items():
            # Map component names to Japanese
            display_base = base_name.replace("pattern_expansion", "パターン展開")
            display_base = display_base.replace("config_compilation", "設定コンパイル")
            display_base = display_base.replace("kernel_cache", "カーネルキャッシュ")

            lines.append(f"\n### {display_base}")

            if "fast" in variants and "slow" in variants:
                fast_comp = variants["fast"]
                slow_comp = variants["slow"]
                speed_improvement = fast_comp.metrics.ops_per_sec / max(
                    1, slow_comp.metrics.ops_per_sec
                )

                lines.append(f"- **性能向上:** {speed_improvement:.1f}x speedup")
                lines.append(
                    f"- **高速実装:** {fast_comp.metrics.ops_per_sec:,.0f} ops/s (p95: {fast_comp.metrics.p95_us:.1f}μs)"
                )
                lines.append(
                    f"- **低速実装:** {slow_comp.metrics.ops_per_sec:,.0f} ops/s (p95: {slow_comp.metrics.p95_us:.1f}μs)"
                )

            elif "single" in variants:
                comp = variants["single"]
                lines.append(
                    f"- **スループット:** {comp.metrics.ops_per_sec:,.0f} operations/second"
                )
                lines.append("- **レイテンシ分布:**")
                lines.append(f"  - p50: {comp.metrics.p50_us:.1f}μs")
                lines.append(f"  - p95: {comp.metrics.p95_us:.1f}μs")
                lines.append(f"  - p99: {comp.metrics.p99_us:.1f}μs")

        # Configuration details
        lines.append("\n## ⚙️ テスト設定")
        lines.append(f"- **実行回数:** {config.get('n', 0):,}")
        lines.append(f"- **ウォームアップ:** {config.get('warmup', 0):,}")
        lines.append("- **評価方法:** 3回実行の中央値")

        # Environment info
        if report.diagnostics:
            diag = report.diagnostics
            lines.append("\n## 🖥️ 実行環境")
            lines.append(
                f"- **Python:** {diag.get('python_version', 'unknown').split()[0]}"
            )
            lines.append(f"- **プラットフォーム:** {diag.get('platform', 'unknown')}")
            if "service_patterns" in diag:
                lines.append(
                    f"- **テストデータ:** {diag['service_patterns']} パターン → {diag.get('direct_mappings', 0)} マッピング"
                )

        # Action items for failures
        if not report.passed:
            lines.append("\n## 🚨 対応が必要")
            lines.append("性能回帰が検出されました。以下を検討してください:")
            lines.append("1. **プロファイル実行** - ボトルネックの特定")
            lines.append("2. **変更レビュー** - 最近のアルゴリズム変更確認")
            lines.append("3. **最適化実施** - 低速コンポーネントの改善")
            lines.append("4. **ローカルテスト** - 問題の再現確認")

        return "\n".join(lines)

    def generate_json_enhanced(self, report: BenchmarkReport) -> dict[str, Any]:
        """Generate enhanced JSON with StrataRegula-specific structure."""
        # Maintain StrataRegula backward compatibility
        base_json = {
            "timestamp": report.timestamp,
            "config": report.config,
            "passed": report.passed,
            "comparison": report.comparison,
        }

        if report.error:
            base_json["error"] = report.error
        if report.diagnostics:
            base_json["diagnostics"] = report.diagnostics

        # Enhanced component data in StrataRegula format
        base_json["components"] = []
        benchmarks = {}

        # Group components by base name for benchmarks object
        for component in report.components:
            base_name = component.name.replace("_fast", "").replace("_slow", "")
            if base_name not in benchmarks:
                benchmarks[base_name] = {}

            comp_data = {
                "ops": component.metrics.ops_per_sec,
                "p50_us": component.metrics.p50_us,
                "p95_us": component.metrics.p95_us,
                "p99_us": component.metrics.p99_us,
            }

            if component.metrics.min_us is not None:
                comp_data["min_us"] = component.metrics.min_us
            if component.metrics.max_us is not None:
                comp_data["max_us"] = component.metrics.max_us
            if component.metrics.mean_us is not None:
                comp_data["mean_us"] = component.metrics.mean_us
            if component.metrics.std_us is not None:
                comp_data["std_us"] = component.metrics.std_us

            if "_fast" in component.name:
                benchmarks[base_name]["fast"] = comp_data
                benchmarks[base_name]["ratio"] = component.metrics.ops_per_sec / max(
                    1,
                    next(
                        (
                            c.metrics.ops_per_sec
                            for c in report.components
                            if c.name.endswith("_slow")
                        ),
                        1,
                    ),
                )
            elif "_slow" in component.name:
                benchmarks[base_name]["slow"] = comp_data
            else:
                benchmarks[base_name]["single"] = comp_data

            # Enhanced component list
            enhanced_comp = {
                "name": component.name,
                "metrics": asdict(component.metrics),
            }
            if component.runs:
                enhanced_comp["runs"] = component.runs
            if component.median_time_s:
                enhanced_comp["median_time_s"] = component.median_time_s
            base_json["components"].append(enhanced_comp)

        base_json["benchmarks"] = benchmarks

        # Backward compatibility - maintain existing fast/slow structure
        fast_components = [
            c
            for c in report.components
            if "_fast" in c.name
            or not any("_slow" in comp.name for comp in report.components)
        ]
        slow_components = [c for c in report.components if "_slow" in c.name]

        if fast_components:
            fastest = max(fast_components, key=lambda c: c.metrics.ops_per_sec)
            base_json["fast"] = {
                "name": fastest.name,
                "ops": fastest.metrics.ops_per_sec,
                "p50_us": fastest.metrics.p50_us,
                "p95_us": fastest.metrics.p95_us,
                "p99_us": fastest.metrics.p99_us,
            }

        if slow_components:
            slowest = min(slow_components, key=lambda c: c.metrics.ops_per_sec)
            base_json["slow"] = {
                "name": slowest.name,
                "ops": slowest.metrics.ops_per_sec,
                "p50_us": slowest.metrics.p50_us,
                "p95_us": slowest.metrics.p95_us,
                "p99_us": slowest.metrics.p99_us,
            }

        # Add reporting metadata
        base_json["_reporting"] = {
            "version": "1.0.0-strataregula",
            "formats_available": ["json", "markdown", "console"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "schema_compatible": True,
            "project": "strataregula",
        }

        return base_json

    def write_outputs(
        self,
        report: BenchmarkReport,
        formats: list[OutputFormat] | None = None,
        base_filename: str = "bench_guard",
    ) -> dict[str, Path]:
        """Write benchmark report in multiple formats."""
        if formats is None:
            formats = [OutputFormat.ALL]

        if OutputFormat.ALL in formats:
            formats = [OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.CONSOLE]

        output_files = {}

        for fmt in formats:
            if fmt == OutputFormat.JSON:
                json_data = self.generate_json_enhanced(report)
                json_path = self.output_dir / f"{base_filename}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                output_files["json"] = json_path

            elif fmt == OutputFormat.MARKDOWN:
                md_content = self.generate_markdown_report(report)
                md_path = self.output_dir / f"{base_filename}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                output_files["markdown"] = md_path

            elif fmt == OutputFormat.CONSOLE:
                console_content = self.generate_console_output(report)
                console_path = self.output_dir / f"{base_filename}_console.txt"
                with open(console_path, "w", encoding="utf-8") as f:
                    f.write(console_content)
                output_files["console"] = console_path
                # Safe print to stdout for immediate feedback
                self._safe_print(console_content)

        return output_files

    def create_ci_summary(self, report: BenchmarkReport) -> str:
        """Create GitHub Actions step summary for StrataRegula."""
        status_emoji = "✅" if report.passed else "❌"
        status_text = "合格" if report.passed else "不合格"

        lines = [
            f"## 🏯 StrataRegula Bench Guard - {status_emoji} {status_text}",
            f"_性能回帰テスト完了: {report.timestamp}_",
            "",
            "### 📊 クイックサマリー",
        ]

        # Key metrics table
        lines.extend(
            [
                "| コンポーネント | 性能 | p95レイテンシ | 状態 |",
                "|-------------|------|-------------|------|",
            ]
        )

        for component in report.components:
            name = component.name.replace("_fast", "（高速）").replace(
                "_slow", "（低速）"
            )
            name = (
                name.replace("pattern_expansion", "パターン展開")
                .replace("config_compilation", "設定コンパイル")
                .replace("kernel_cache", "カーネルキャッシュ")
            )
            ops_k = component.metrics.ops_per_sec / 1000
            status = (
                "🟢"
                if component.metrics.p95_us <= 50
                else "🟡"
                if component.metrics.p95_us <= 100
                else "🔴"
            )
            lines.append(
                f"| **{name}** | {ops_k:.0f}K ops/s | {component.metrics.p95_us:.1f}μs | {status} |"
            )

        # Threshold status
        comparison = report.comparison
        config = report.config
        ratio_status = "✅" if comparison.get("ratio_ok", False) else "❌"
        p95_status = "✅" if comparison.get("fast_p95_ok", False) else "❌"

        lines.extend(
            [
                "",
                "### 🎯 閾値適合性",
                f"- {ratio_status} **速度比:** {comparison.get('ratio_fast_over_slow', 0):.1f}x (要求: ≥{config.get('min_ratio', 0)}x)",
                f"- {p95_status} **最大p95レイテンシ:** {max((c.metrics.p95_us for c in report.components), default=0):.1f}μs (要求: ≤{config.get('max_p95_us', 0)}μs)",
            ]
        )

        # Failure details
        if not report.passed:
            lines.extend(
                ["", "### ❌ 回帰詳細", "**このPRは性能回帰を引き起こしています:**"]
            )

            if not comparison.get("ratio_ok", True):
                lines.append(
                    f"- 速度が{config.get('min_ratio', 0)}x閾値を下回っています"
                )
            if not comparison.get("fast_p95_ok", True):
                lines.append(
                    f"- レイテンシが{config.get('max_p95_us', 0)}μs制限を超えています"
                )

            lines.extend(
                [
                    "",
                    "**次のステップ:**",
                    "1. `python bench_guard.py` をローカルで実行して再現確認",
                    "2. 影響を受けたコンポーネントのプロファイル実行",
                    "3. クリティカルパスの最適化または閾値調整",
                ]
            )

        return "\n".join(lines)


def main():
    """CLI interface for StrataRegula enhanced benchmark reporting."""
    import argparse

    parser = argparse.ArgumentParser(
        description="StrataRegula multi-format benchmark reporter"
    )
    parser.add_argument(
        "input_json",
        nargs="?",
        default="bench_guard.json",
        help="Input JSON benchmark results file",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "console", "all"],
        default="all",
        help="Output format(s)",
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument(
        "--base-name", default="bench_guard", help="Base filename for outputs"
    )
    parser.add_argument(
        "--ci-summary", action="store_true", help="Generate GitHub Actions step summary"
    )
    parser.add_argument(
        "--auto-ci",
        action="store_true",
        help="Auto-detect CI environment and optimize output",
    )

    args = parser.parse_args()

    input_path = Path(args.input_json)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        reporter = StrataRegulaReporter(args.output_dir)
        report = reporter.load_json_results(input_path)

        # Auto-detect CI environment
        if args.auto_ci and (os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI")):
            format_enum = [OutputFormat.JSON, OutputFormat.MARKDOWN]
            args.ci_summary = True
        else:
            format_enum = [OutputFormat(args.format)]

        # Generate requested formats
        output_files = reporter.write_outputs(report, format_enum, args.base_name)

        # Generate CI summary if requested
        if args.ci_summary:
            ci_summary = reporter.create_ci_summary(report)

            # Append to GitHub step summary if in CI environment
            if os.getenv("GITHUB_STEP_SUMMARY"):
                with open(os.getenv("GITHUB_STEP_SUMMARY"), "a", encoding="utf-8") as f:
                    f.write(ci_summary)
                print("GitHub step summary updated")
            else:
                # Write to file for local development
                summary_path = reporter.output_dir / f"{args.base_name}_ci_summary.md"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(ci_summary)
                output_files["ci_summary"] = summary_path

        # Report generated files (safe print)
        print(f"\nGenerated {len(output_files)} output files:")
        for fmt, path in output_files.items():
            print(f"   * {fmt}: {path}")

        return 0 if report.passed else 1

    except Exception as e:
        print(f"Reporter failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

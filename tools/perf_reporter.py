#!/usr/bin/env python3
"""
Performance Results Storage and Analysis System

Provides centralized storage, retrieval, and analysis of performance benchmark results
across Python and PowerShell implementations. Supports:

- Historical performance tracking
- Trend analysis and visualization
- Performance regression detection
- Cross-language performance comparison
- Automated report generation

Usage:
    python tools/perf_reporter.py --analyze --days 30
    python tools/perf_reporter.py --report --format html
    python tools/perf_reporter.py --compare python powershell
    python tools/perf_reporter.py --regression-check --tolerance 10
"""

import argparse
import json
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


class PerformanceDatabase:
    """SQLite-based storage for performance metrics with efficient querying"""

    def __init__(self, db_path: str = "benchmarks/performance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    benchmark_name TEXT NOT NULL,
                    language TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    mean_time_us REAL,
                    p95_time_us REAL,
                    p99_time_us REAL,
                    ops_per_second REAL,
                    memory_delta_mb REAL,
                    performance_class TEXT,
                    system_info TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_benchmark_runs_name_time
                ON benchmark_runs(benchmark_name, timestamp);

                CREATE INDEX IF NOT EXISTS idx_benchmark_runs_language
                ON benchmark_runs(language, benchmark_name);

                CREATE TABLE IF NOT EXISTS performance_baselines (
                    benchmark_name TEXT PRIMARY KEY,
                    language TEXT NOT NULL,
                    baseline_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS regression_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    benchmark_suite TEXT NOT NULL,
                    passed BOOLEAN NOT NULL,
                    regression_count INTEGER,
                    improvement_count INTEGER,
                    tolerance_percent REAL,
                    results_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def store_benchmark_results(
        self, benchmark_name: str, language: str, results: dict[str, Any]
    ) -> None:
        """Store benchmark results in database"""

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Handle both single test and multiple test results
            if "functions" in results:
                # Module benchmark with multiple functions
                for test_name, metrics in results["functions"].items():
                    if "error" not in metrics:
                        self._insert_benchmark_record(
                            conn,
                            timestamp,
                            benchmark_name,
                            language,
                            test_name,
                            metrics,
                        )
            elif "implementations" in results:
                # Comparison benchmark
                for impl_name, metrics in results["implementations"].items():
                    if "error" not in metrics:
                        self._insert_benchmark_record(
                            conn,
                            timestamp,
                            f"{benchmark_name}_comparison",
                            language,
                            impl_name,
                            metrics,
                        )
            # Single function benchmark
            elif "error" not in results:
                self._insert_benchmark_record(
                    conn,
                    timestamp,
                    benchmark_name,
                    language,
                    benchmark_name,
                    results,
                )

    def _insert_benchmark_record(
        self,
        conn: sqlite3.Connection,
        timestamp: str,
        benchmark_name: str,
        language: str,
        test_name: str,
        metrics: dict[str, Any],
    ) -> None:
        """Insert individual benchmark record"""

        # Extract metrics with safe defaults
        mean_time_us = metrics.get("mean_us") or metrics.get("MeanMicroseconds", 0)
        p95_time_us = metrics.get("p95_us") or metrics.get("P95Microseconds", 0)
        p99_time_us = metrics.get("p99_us") or metrics.get("P99Microseconds", 0)
        ops_per_second = metrics.get("ops_per_second") or metrics.get(
            "OperationsPerSecond", 0
        )
        memory_delta_mb = metrics.get("memory_delta_mb") or metrics.get(
            "MemoryDeltaMB", 0
        )
        performance_class = metrics.get("performance_class") or metrics.get(
            "PerformanceClass", "unknown"
        )

        # Store system info and metadata as JSON
        system_info = json.dumps(metrics.get("system_info", {}))
        metadata = json.dumps(
            {
                k: v
                for k, v in metrics.items()
                if k
                not in [
                    "mean_us",
                    "p95_us",
                    "p99_us",
                    "ops_per_second",
                    "memory_delta_mb",
                    "performance_class",
                    "system_info",
                ]
            }
        )

        conn.execute(
            """
            INSERT INTO benchmark_runs
            (timestamp, benchmark_name, language, test_name, mean_time_us, p95_time_us, p99_time_us,
             ops_per_second, memory_delta_mb, performance_class, system_info, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                benchmark_name,
                language,
                test_name,
                mean_time_us,
                p95_time_us,
                p99_time_us,
                ops_per_second,
                memory_delta_mb,
                performance_class,
                system_info,
                metadata,
            ),
        )

    def get_benchmark_history(
        self, benchmark_name: str, days: int = 30, language: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve benchmark history for analysis"""

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT * FROM benchmark_runs
            WHERE benchmark_name = ? AND timestamp >= ?
        """
        params = [benchmark_name, cutoff_date]

        if language:
            query += " AND language = ?"
            params.append(language)

        query += " ORDER BY timestamp"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_results(
        self, benchmark_name: str, language: str | None = None
    ) -> dict[str, Any]:
        """Get most recent benchmark results"""

        query = """
            SELECT * FROM benchmark_runs
            WHERE benchmark_name = ?
        """
        params = [benchmark_name]

        if language:
            query += " AND language = ?"
            params.append(language)

        query += " ORDER BY timestamp DESC LIMIT 10"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return {}

            # Group by test_name for latest run
            latest_timestamp = rows[0]["timestamp"]
            latest_results = {}

            for row in rows:
                if row["timestamp"] == latest_timestamp:
                    latest_results[row["test_name"]] = dict(row)

            return latest_results

    def store_regression_result(
        self,
        benchmark_suite: str,
        passed: bool,
        regression_count: int,
        improvement_count: int,
        tolerance_percent: float,
        full_results: dict[str, Any],
    ) -> None:
        """Store regression test results"""

        timestamp = datetime.now().isoformat()
        results_json = json.dumps(full_results)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO regression_results
                (timestamp, benchmark_suite, passed, regression_count, improvement_count,
                 tolerance_percent, results_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    benchmark_suite,
                    passed,
                    regression_count,
                    improvement_count,
                    tolerance_percent,
                    results_json,
                ),
            )

    def get_regression_history(self, days: int = 30) -> list[dict[str, Any]]:
        """Get regression test history"""

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM regression_results
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (cutoff_date,),
            )

            return [dict(row) for row in cursor.fetchall()]


class TrendAnalyzer:
    """Analyze performance trends over time"""

    def __init__(self, db: PerformanceDatabase):
        self.db = db

    def analyze_performance_trends(
        self, benchmark_name: str, days: int = 30
    ) -> dict[str, Any]:
        """Comprehensive trend analysis for a benchmark"""

        # Get historical data
        history = self.db.get_benchmark_history(benchmark_name, days)

        if len(history) < 2:
            return {
                "error": f"Insufficient data for trend analysis (found {len(history)} records)"
            }

        # Convert to pandas for easier analysis
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Analyze trends for each test
        test_trends = {}
        for test_name in df["test_name"].unique():
            test_data = df[df["test_name"] == test_name]
            test_trends[test_name] = self._analyze_single_test_trend(test_data)

        # Overall benchmark analysis
        overall_analysis = self._analyze_overall_trends(df)

        return {
            "benchmark_name": benchmark_name,
            "analysis_period_days": days,
            "total_data_points": len(history),
            "test_trends": test_trends,
            "overall_analysis": overall_analysis,
            "trend_summary": self._generate_trend_summary(test_trends),
        }

    def _analyze_single_test_trend(self, test_data: pd.DataFrame) -> dict[str, Any]:
        """Analyze trend for a single test function"""

        if len(test_data) < 2:
            return {"error": "Insufficient data"}

        # Time series analysis
        times = test_data["mean_time_us"].values
        timestamps = test_data["timestamp"].values

        # Calculate trend
        slope = self._calculate_trend_slope(times)

        # Recent vs historical comparison
        recent_count = max(1, len(times) // 4)  # Last 25% of data
        recent_times = times[-recent_count:]
        historical_times = times[:-recent_count] if len(times) > recent_count else times

        recent_avg = statistics.mean(recent_times)
        historical_avg = (
            statistics.mean(historical_times) if historical_times else recent_avg
        )

        # Performance stability
        cv = statistics.stdev(recent_times) / recent_avg if recent_avg > 0 else 0

        return {
            "data_points": len(test_data),
            "time_span_days": (timestamps[-1] - timestamps[0]).days,
            "trend_direction": "improving"
            if slope < -0.01
            else "degrading"
            if slope > 0.01
            else "stable",
            "slope_us_per_day": slope,
            "recent_average_us": recent_avg,
            "historical_average_us": historical_avg,
            "change_percent": ((recent_avg - historical_avg) / historical_avg * 100)
            if historical_avg > 0
            else 0,
            "stability_coefficient": cv,
            "stability_rating": self._classify_stability(cv),
            "performance_class": self._classify_performance(recent_avg),
        }

    def _analyze_overall_trends(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze overall benchmark trends"""

        # Group by timestamp to get overall performance per run
        by_timestamp = (
            df.groupby("timestamp")
            .agg(
                {
                    "mean_time_us": "mean",
                    "ops_per_second": "sum",
                    "memory_delta_mb": "sum",
                }
            )
            .reset_index()
        )

        # Overall trend analysis
        overall_performance = by_timestamp["mean_time_us"].values
        overall_throughput = by_timestamp["ops_per_second"].values
        overall_memory = by_timestamp["memory_delta_mb"].values

        return {
            "performance_trend": self._calculate_trend_slope(overall_performance),
            "throughput_trend": self._calculate_trend_slope(overall_throughput),
            "memory_trend": self._calculate_trend_slope(overall_memory),
            "average_performance_us": statistics.mean(overall_performance),
            "average_throughput_ops": statistics.mean(overall_throughput),
            "average_memory_mb": statistics.mean(overall_memory),
            "performance_variance": statistics.variance(overall_performance)
            if len(overall_performance) > 1
            else 0,
        }

    def _calculate_trend_slope(self, values: list[float]) -> float:
        """Calculate trend slope using linear regression"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_values = list(range(n))

        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        return numerator / denominator if denominator != 0 else 0.0

    def _classify_stability(self, coefficient_of_variation: float) -> str:
        """Classify performance stability"""
        if coefficient_of_variation < 0.05:
            return "very_stable"
        elif coefficient_of_variation < 0.1:
            return "stable"
        elif coefficient_of_variation < 0.2:
            return "moderate"
        else:
            return "unstable"

    def _classify_performance(self, mean_time_us: float) -> str:
        """Classify performance level"""
        if mean_time_us < 10:
            return "excellent"
        elif mean_time_us < 100:
            return "good"
        elif mean_time_us < 1000:
            return "acceptable"
        elif mean_time_us < 10000:
            return "slow"
        else:
            return "very_slow"

    def _generate_trend_summary(self, test_trends: dict[str, Any]) -> dict[str, Any]:
        """Generate summary of all test trends"""

        valid_trends = {k: v for k, v in test_trends.items() if "error" not in v}

        if not valid_trends:
            return {"error": "No valid trend data"}

        # Categorize trends
        improving = [
            k for k, v in valid_trends.items() if v["trend_direction"] == "improving"
        ]
        degrading = [
            k for k, v in valid_trends.items() if v["trend_direction"] == "degrading"
        ]
        stable = [
            k for k, v in valid_trends.items() if v["trend_direction"] == "stable"
        ]

        # Overall health assessment
        degrading_pct = len(degrading) / len(valid_trends) * 100
        health_status = (
            "healthy"
            if degrading_pct < 20
            else "concerning"
            if degrading_pct < 50
            else "critical"
        )

        return {
            "total_tests": len(valid_trends),
            "improving_tests": len(improving),
            "degrading_tests": len(degrading),
            "stable_tests": len(stable),
            "degrading_percentage": degrading_pct,
            "health_status": health_status,
            "improving_test_names": improving,
            "degrading_test_names": degrading,
            "recommendations": self._generate_recommendations(valid_trends),
        }

    def _generate_recommendations(self, trends: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations based on trends"""
        recommendations = []

        # Identify consistently degrading tests
        degrading_tests = [
            k
            for k, v in trends.items()
            if v["trend_direction"] == "degrading" and v["change_percent"] > 20
        ]

        if degrading_tests:
            recommendations.append(
                f"🚨 Priority: Investigate degrading tests: {', '.join(degrading_tests)}"
            )

        # Identify unstable tests
        unstable_tests = [
            k
            for k, v in trends.items()
            if v["stability_rating"] in ["moderate", "unstable"]
        ]

        if unstable_tests:
            recommendations.append(
                f"📊 Stability: Review inconsistent tests: {', '.join(unstable_tests)}"
            )

        # Identify slow tests
        slow_tests = [
            k
            for k, v in trends.items()
            if v["performance_class"] in ["slow", "very_slow"]
        ]

        if slow_tests:
            recommendations.append(
                f"⚡ Performance: Optimize slow tests: {', '.join(slow_tests)}"
            )

        if not recommendations:
            recommendations.append(
                "✅ All tests performing within acceptable parameters"
            )

        return recommendations


class CrossLanguageComparator:
    """Compare performance across Python and PowerShell implementations"""

    def __init__(self, db: PerformanceDatabase):
        self.db = db

    def compare_languages(self, benchmark_name: str, days: int = 7) -> dict[str, Any]:
        """Compare Python vs PowerShell performance for same functionality"""

        # Get recent data for both languages
        python_data = self.db.get_benchmark_history(benchmark_name, days, "python")
        powershell_data = self.db.get_benchmark_history(
            benchmark_name, days, "powershell"
        )

        if not python_data and not powershell_data:
            return {"error": f"No data found for benchmark: {benchmark_name}"}

        comparison = {
            "benchmark_name": benchmark_name,
            "analysis_period_days": days,
            "languages_compared": [],
        }

        # Analyze each language
        if python_data:
            comparison["python_analysis"] = self._analyze_language_performance(
                python_data, "python"
            )
            comparison["languages_compared"].append("python")

        if powershell_data:
            comparison["powershell_analysis"] = self._analyze_language_performance(
                powershell_data, "powershell"
            )
            comparison["languages_compared"].append("powershell")

        # Direct comparison if both languages have data
        if python_data and powershell_data:
            comparison["direct_comparison"] = self._direct_language_comparison(
                python_data, powershell_data
            )

        return comparison

    def _analyze_language_performance(
        self, data: list[dict], language: str
    ) -> dict[str, Any]:
        """Analyze performance characteristics for a single language"""

        if not data:
            return {"error": f"No data for {language}"}

        # Extract timing data
        timing_data = [
            record["mean_time_us"] for record in data if record["mean_time_us"]
        ]
        throughput_data = [
            record["ops_per_second"] for record in data if record["ops_per_second"]
        ]
        memory_data = [
            record["memory_delta_mb"] for record in data if record["memory_delta_mb"]
        ]

        analysis = {
            "language": language,
            "data_points": len(data),
            "unique_tests": len({record["test_name"] for record in data}),
        }

        if timing_data:
            analysis["timing_analysis"] = {
                "average_time_us": statistics.mean(timing_data),
                "median_time_us": statistics.median(timing_data),
                "time_variability": statistics.stdev(timing_data)
                / statistics.mean(timing_data)
                if len(timing_data) > 1
                else 0,
                "performance_consistency": self._classify_consistency(timing_data),
            }

        if throughput_data:
            analysis["throughput_analysis"] = {
                "average_ops_per_sec": statistics.mean(throughput_data),
                "peak_throughput": max(throughput_data),
                "throughput_stability": statistics.stdev(throughput_data)
                / statistics.mean(throughput_data)
                if len(throughput_data) > 1
                else 0,
            }

        if memory_data:
            analysis["memory_analysis"] = {
                "average_memory_mb": statistics.mean(memory_data),
                "peak_memory_mb": max(memory_data),
                "memory_efficiency": self._calculate_memory_efficiency(
                    memory_data, timing_data
                ),
            }

        return analysis

    def _direct_language_comparison(
        self, python_data: list[dict], powershell_data: list[dict]
    ) -> dict[str, Any]:
        """Direct performance comparison between languages"""

        # Get recent averages for comparison
        recent_python = python_data[-10:] if len(python_data) >= 10 else python_data
        recent_powershell = (
            powershell_data[-10:] if len(powershell_data) >= 10 else powershell_data
        )

        python_avg_time = statistics.mean(
            [r["mean_time_us"] for r in recent_python if r["mean_time_us"]]
        )
        powershell_avg_time = statistics.mean(
            [r["mean_time_us"] for r in recent_powershell if r["mean_time_us"]]
        )

        python_avg_throughput = statistics.mean(
            [r["ops_per_second"] for r in recent_python if r["ops_per_second"]]
        )
        powershell_avg_throughput = statistics.mean(
            [r["ops_per_second"] for r in recent_powershell if r["ops_per_second"]]
        )

        # Determine winner and margins
        timing_winner = (
            "python" if python_avg_time < powershell_avg_time else "powershell"
        )
        timing_margin = (
            abs(python_avg_time - powershell_avg_time)
            / min(python_avg_time, powershell_avg_time)
            * 100
        )

        throughput_winner = (
            "python"
            if python_avg_throughput > powershell_avg_throughput
            else "powershell"
        )
        throughput_margin = (
            abs(python_avg_throughput - powershell_avg_throughput)
            / max(python_avg_throughput, powershell_avg_throughput)
            * 100
        )

        return {
            "timing_comparison": {
                "python_avg_us": python_avg_time,
                "powershell_avg_us": powershell_avg_time,
                "winner": timing_winner,
                "margin_percent": timing_margin,
                "speed_ratio": max(python_avg_time, powershell_avg_time)
                / min(python_avg_time, powershell_avg_time),
            },
            "throughput_comparison": {
                "python_ops_per_sec": python_avg_throughput,
                "powershell_ops_per_sec": powershell_avg_throughput,
                "winner": throughput_winner,
                "margin_percent": throughput_margin,
            },
            "overall_recommendation": self._generate_language_recommendation(
                timing_winner, timing_margin, throughput_winner, throughput_margin
            ),
        }

    def _classify_consistency(self, timing_data: list[float]) -> str:
        """Classify performance consistency"""
        if len(timing_data) < 2:
            return "insufficient_data"

        cv = statistics.stdev(timing_data) / statistics.mean(timing_data)
        return self.db._classify_stability(cv)

    def _calculate_memory_efficiency(
        self, memory_data: list[float], timing_data: list[float]
    ) -> float:
        """Calculate memory efficiency score"""
        if not memory_data or not timing_data:
            return 0.0

        avg_memory = statistics.mean(memory_data)
        avg_time = statistics.mean(timing_data)

        # Efficiency = work done per memory used
        return avg_time / max(avg_memory, 0.001)  # Avoid division by zero

    def _generate_language_recommendation(
        self,
        timing_winner: str,
        timing_margin: float,
        throughput_winner: str,
        throughput_margin: float,
    ) -> str:
        """Generate recommendation for language choice"""

        if timing_winner == throughput_winner and timing_margin > 20:
            return f"Strong preference for {timing_winner} (significant performance advantage)"
        elif timing_winner == throughput_winner and timing_margin > 10:
            return f"Moderate preference for {timing_winner} (measurable performance advantage)"
        elif timing_margin < 10 and throughput_margin < 10:
            return "Performance parity - choose based on maintainability and ecosystem"
        else:
            return f"Mixed results - {timing_winner} faster execution, {throughput_winner} higher throughput"


class ReportGenerator:
    """Generate comprehensive performance reports"""

    def __init__(self, db: PerformanceDatabase, analyzer: TrendAnalyzer):
        self.db = db
        self.analyzer = analyzer

    def generate_comprehensive_report(
        self, days: int = 30, format: str = "json"
    ) -> dict[str, Any]:
        """Generate comprehensive performance report"""

        # Get all unique benchmark names
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT benchmark_name FROM benchmark_runs")
            benchmark_names = [row[0] for row in cursor.fetchall()]

        report = {
            "report_type": "comprehensive_performance_analysis",
            "generated_at": datetime.now().isoformat(),
            "analysis_period_days": days,
            "benchmarks_analyzed": len(benchmark_names),
            "benchmark_analyses": {},
            "cross_language_comparisons": {},
            "regression_summary": self._get_regression_summary(days),
            "overall_health": {},
        }

        # Analyze each benchmark
        for benchmark_name in benchmark_names:
            print(f"Analyzing benchmark: {benchmark_name}")

            # Trend analysis
            trend_analysis = self.analyzer.analyze_performance_trends(
                benchmark_name, days
            )
            report["benchmark_analyses"][benchmark_name] = trend_analysis

            # Cross-language comparison if applicable
            cross_lang = self.analyzer.compare_languages(benchmark_name, days)
            if (
                "error" not in cross_lang
                and len(cross_lang.get("languages_compared", [])) > 1
            ):
                report["cross_language_comparisons"][benchmark_name] = cross_lang

        # Overall health assessment
        report["overall_health"] = self._assess_overall_health(
            report["benchmark_analyses"]
        )

        return report

    def _get_regression_summary(self, days: int) -> dict[str, Any]:
        """Get summary of recent regression tests"""

        regression_history = self.db.get_regression_history(days)

        if not regression_history:
            return {"status": "no_regression_tests_found"}

        recent_tests = regression_history[:10]  # Last 10 tests
        passed_count = sum(1 for test in recent_tests if test["passed"])

        return {
            "total_regression_tests": len(regression_history),
            "recent_tests_analyzed": len(recent_tests),
            "recent_pass_rate": (passed_count / len(recent_tests)) * 100,
            "last_test_status": "passed" if recent_tests[0]["passed"] else "failed",
            "last_test_timestamp": recent_tests[0]["timestamp"],
            "trend": self._analyze_regression_trend(recent_tests),
        }

    def _analyze_regression_trend(self, recent_tests: list[dict]) -> str:
        """Analyze trend in regression test results"""

        if len(recent_tests) < 3:
            return "insufficient_data"

        # Look at last 5 vs previous tests
        last_5 = recent_tests[:5]
        previous = recent_tests[5:]

        recent_pass_rate = sum(1 for test in last_5 if test["passed"]) / len(last_5)
        previous_pass_rate = (
            sum(1 for test in previous if test["passed"]) / len(previous)
            if previous
            else recent_pass_rate
        )

        if recent_pass_rate > previous_pass_rate + 0.2:
            return "improving"
        elif recent_pass_rate < previous_pass_rate - 0.2:
            return "degrading"
        else:
            return "stable"

    def _assess_overall_health(
        self, benchmark_analyses: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess overall performance health across all benchmarks"""

        valid_analyses = {
            k: v for k, v in benchmark_analyses.items() if "error" not in v
        }

        if not valid_analyses:
            return {"status": "no_valid_data"}

        # Aggregate health metrics
        total_tests = sum(
            analysis.get("test_trends", {}).keys().__len__()
            for analysis in valid_analyses.values()
        )

        degrading_count = 0
        slow_count = 0
        unstable_count = 0

        for analysis in valid_analyses.values():
            test_trends = analysis.get("test_trends", {})
            for _test_name, trend in test_trends.items():
                if trend.get("trend_direction") == "degrading":
                    degrading_count += 1
                if trend.get("performance_class") in ["slow", "very_slow"]:
                    slow_count += 1
                if trend.get("stability_rating") in ["moderate", "unstable"]:
                    unstable_count += 1

        # Calculate health score
        degrading_pct = (degrading_count / total_tests) * 100 if total_tests > 0 else 0
        slow_pct = (slow_count / total_tests) * 100 if total_tests > 0 else 0
        unstable_pct = (unstable_count / total_tests) * 100 if total_tests > 0 else 0

        health_score = 100 - (degrading_pct * 2 + slow_pct + unstable_pct * 0.5)
        health_score = max(0, min(100, health_score))

        return {
            "health_score": health_score,
            "total_tests_analyzed": total_tests,
            "degrading_tests": degrading_count,
            "slow_tests": slow_count,
            "unstable_tests": unstable_count,
            "health_rating": self._classify_health(health_score),
            "priority_actions": self._generate_priority_actions(
                degrading_pct, slow_pct, unstable_pct
            ),
        }

    def _classify_health(self, health_score: float) -> str:
        """Classify overall health rating"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "concerning"
        else:
            return "critical"

    def _generate_priority_actions(
        self, degrading_pct: float, slow_pct: float, unstable_pct: float
    ) -> list[str]:
        """Generate priority actions based on health metrics"""
        actions = []

        if degrading_pct > 20:
            actions.append(
                "🚨 HIGH PRIORITY: Address performance regressions immediately"
            )
        elif degrading_pct > 10:
            actions.append(
                "⚠️ MEDIUM PRIORITY: Monitor and address performance degradation"
            )

        if slow_pct > 30:
            actions.append(
                "⚡ OPTIMIZATION: Significant number of slow operations need attention"
            )
        elif slow_pct > 15:
            actions.append("📈 IMPROVEMENT: Consider optimizing slow operations")

        if unstable_pct > 25:
            actions.append("📊 STABILITY: Address inconsistent performance patterns")

        if not actions:
            actions.append("✅ MAINTAIN: Continue current performance practices")

        return actions

    def export_report(
        self,
        report: dict[str, Any],
        format: str = "json",
        output_file: str | None = None,
    ) -> str:
        """Export report in specified format"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not output_file:
            output_file = f"benchmarks/reports/performance_report_{timestamp}.{format}"

        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)

        if format == "json":
            output_path.write_text(json.dumps(report, indent=2))

        elif format == "html":
            html_content = self._generate_html_report(report)
            output_path.write_text(html_content)

        elif format == "markdown":
            markdown_content = self._generate_markdown_report(report)
            output_path.write_text(markdown_content)

        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(output_path)

    def _generate_html_report(self, report: dict[str, Any]) -> str:
        """Generate HTML report"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Strataregula Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f8ff; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }}
        .healthy {{ background-color: #d4edda; }}
        .warning {{ background-color: #fff3cd; }}
        .critical {{ background-color: #f8d7da; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Strataregula Performance Report</h1>
        <p>Generated: {report["generated_at"]}</p>
        <p>Analysis Period: {report["analysis_period_days"]} days</p>
    </div>

    <div class="section">
        <h2>Overall Health</h2>
        <div class="metric {self._get_health_css_class(report["overall_health"].get("health_rating", "unknown"))}">
            <strong>Health Score: {report["overall_health"].get("health_score", 0):.1f}/100</strong><br>
            Rating: {report["overall_health"].get("health_rating", "unknown").title()}
        </div>
    </div>

    <div class="section">
        <h2>Benchmark Summary</h2>
        <table>
            <tr><th>Benchmark</th><th>Tests</th><th>Health</th><th>Trend</th></tr>
        """

        for name, analysis in report["benchmark_analyses"].items():
            if "error" not in analysis:
                trend_summary = analysis.get("trend_summary", {})
                health = trend_summary.get("health_status", "unknown")
                test_count = trend_summary.get("total_tests", 0)

                html += f"""
            <tr>
                <td>{name}</td>
                <td>{test_count}</td>
                <td class="{self._get_health_css_class(health)}">{health.title()}</td>
                <td>{analysis.get("overall_analysis", {}).get("performance_trend", "unknown")}</td>
            </tr>
                """

        html += """
        </table>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ul>
        """

        for analysis in report["benchmark_analyses"].values():
            if "error" not in analysis:
                for rec in analysis.get("trend_summary", {}).get("recommendations", []):
                    html += f"<li>{rec}</li>"

        html += """
        </ul>
    </div>
</body>
</html>
        """

        return html

    def _get_health_css_class(self, health_rating: str) -> str:
        """Get CSS class for health rating"""
        if health_rating in ["excellent", "good", "healthy"]:
            return "healthy"
        elif health_rating in ["concerning", "moderate"]:
            return "warning"
        else:
            return "critical"

    def _generate_markdown_report(self, report: dict[str, Any]) -> str:
        """Generate Markdown report"""

        md = f"""# Strataregula Performance Report

**Generated:** {report["generated_at"]}
**Analysis Period:** {report["analysis_period_days"]} days
**Benchmarks Analyzed:** {report["benchmarks_analyzed"]}

## Overall Health Status

**Health Score:** {report["overall_health"].get("health_score", 0):.1f}/100
**Rating:** {report["overall_health"].get("health_rating", "unknown").title()}

### Health Metrics
- Total Tests: {report["overall_health"].get("total_tests_analyzed", 0)}
- Degrading Tests: {report["overall_health"].get("degrading_tests", 0)}
- Slow Tests: {report["overall_health"].get("slow_tests", 0)}
- Unstable Tests: {report["overall_health"].get("unstable_tests", 0)}

## Benchmark Analysis

"""

        for name, analysis in report["benchmark_analyses"].items():
            if "error" not in analysis:
                trend_summary = analysis.get("trend_summary", {})

                md += f"""### {name}

**Health Status:** {trend_summary.get("health_status", "unknown").title()}
**Tests:** {trend_summary.get("total_tests", 0)}
**Improving:** {trend_summary.get("improving_tests", 0)}
**Degrading:** {trend_summary.get("degrading_tests", 0)}
**Stable:** {trend_summary.get("stable_tests", 0)}

"""

                recommendations = trend_summary.get("recommendations", [])
                if recommendations:
                    md += "**Recommendations:**\n"
                    for rec in recommendations:
                        md += f"- {rec}\n"
                    md += "\n"

        ## Cross-Language Comparisons

        if report.get("cross_language_comparisons"):
            md += "## Cross-Language Performance\n\n"

            for benchmark_name, comparison in report[
                "cross_language_comparisons"
            ].items():
                if "direct_comparison" in comparison:
                    direct = comparison["direct_comparison"]
                    timing = direct["timing_comparison"]

                    md += f"""### {benchmark_name}

**Timing Winner:** {timing["winner"].title()}
**Speed Advantage:** {timing["margin_percent"]:.1f}%
**Recommendation:** {direct["overall_recommendation"]}

"""

        return md


def import_json_results(file_path: str, db: PerformanceDatabase) -> None:
    """Import performance results from JSON file"""

    results_file = Path(file_path)
    if not results_file.exists():
        print(f"❌ Results file not found: {file_path}")
        return

    try:
        data = json.loads(results_file.read_text())

        # Determine result type and extract metadata
        if "regression_analysis" in data:
            # Regression test results
            analysis = data["regression_analysis"]
            db.store_regression_result(
                benchmark_suite="core_tests",
                passed=analysis["passed"],
                regression_count=len(analysis["regressions"]),
                improvement_count=len(analysis["improvements"]),
                tolerance_percent=data.get("tolerance_pct", 10.0),
                full_results=data,
            )
            print(f"✅ Imported regression test results from {results_file.name}")

        elif "implementations" in data:
            # Comparison results
            benchmark_name = f"comparison_{results_file.stem}"
            language = "mixed"  # Comparison across implementations
            db.store_benchmark_results(benchmark_name, language, data)
            print(f"✅ Imported comparison results as {benchmark_name}")

        elif "core_benchmarks" in data:
            # Comprehensive benchmark results
            core_results = data["core_benchmarks"]
            formatted_results = {"functions": core_results}
            db.store_benchmark_results(
                "comprehensive_suite", "python", formatted_results
            )
            print("✅ Imported comprehensive benchmark results")

        else:
            # Try to auto-detect format
            benchmark_name = results_file.stem
            language = (
                "python"
                if any(key in data for key in ["mean_us", "ops_per_second"])
                else "powershell"
            )
            db.store_benchmark_results(benchmark_name, language, data)
            print(f"✅ Imported {language} results as {benchmark_name}")

    except Exception as e:
        print(f"❌ Failed to import {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Strataregula Performance Reporter")
    parser.add_argument("--analyze", action="store_true", help="Run trend analysis")
    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive report"
    )
    parser.add_argument(
        "--compare", nargs=2, metavar=("LANG1", "LANG2"), help="Compare languages"
    )
    parser.add_argument(
        "--regression-check", action="store_true", help="Check for regressions"
    )
    parser.add_argument("--import-results", help="Import results from JSON file")
    parser.add_argument("--benchmark", help="Specific benchmark to analyze")
    parser.add_argument(
        "--days", type=int, default=30, help="Days of history to analyze"
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "markdown"],
        default="json",
        help="Report format",
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--tolerance", type=float, default=10.0, help="Regression tolerance percentage"
    )

    args = parser.parse_args()

    # Initialize components
    db = PerformanceDatabase()
    analyzer = TrendAnalyzer(db)
    reporter = ReportGenerator(db, analyzer)

    if args.import_results:
        # Import results from file
        import_json_results(args.import_results, db)

    elif args.analyze:
        # Run trend analysis
        benchmark_name = args.benchmark or "comprehensive_suite"

        print(f"🔍 Analyzing trends for {benchmark_name} over {args.days} days...")
        trend_analysis = analyzer.analyze_performance_trends(benchmark_name, args.days)

        if "error" in trend_analysis:
            print(f"❌ {trend_analysis['error']}")
            return

        # Display trend summary
        summary = trend_analysis["trend_summary"]
        print("\n📊 Trend Analysis Results:")
        print(f"Health Status: {summary['health_status'].upper()}")
        print(f"Total Tests: {summary['total_tests']}")
        print(
            f"Improving: {summary['improving_tests']} | Degrading: {summary['degrading_tests']} | Stable: {summary['stable_tests']}"
        )

        if summary["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"  {rec}")

    elif args.report:
        # Generate comprehensive report
        print("📋 Generating comprehensive performance report...")

        report = reporter.generate_comprehensive_report(args.days, args.format)
        output_file = reporter.export_report(report, args.format, args.output)

        print(f"✅ Report generated: {output_file}")

        # Display summary
        health = report["overall_health"]
        print("\n📊 Report Summary:")
        print(
            f"Overall Health Score: {health.get('health_score', 0):.1f}/100 ({health.get('health_rating', 'unknown').upper()})"
        )
        print(f"Benchmarks Analyzed: {report['benchmarks_analyzed']}")
        print(f"Total Tests: {health.get('total_tests_analyzed', 0)}")

    elif args.compare:
        # Cross-language comparison
        lang1, lang2 = args.compare
        benchmark_name = args.benchmark or "core_functionality"

        print(f"⚖️ Comparing {lang1} vs {lang2} for {benchmark_name}...")

        comparison = analyzer.compare_languages(benchmark_name, args.days)

        if "error" in comparison:
            print(f"❌ {comparison['error']}")
            return

        # Display comparison results
        if "direct_comparison" in comparison:
            direct = comparison["direct_comparison"]
            timing = direct["timing_comparison"]

            print("\n🏆 Performance Comparison:")
            print(
                f"Timing Winner: {timing['winner'].upper()} ({timing['margin_percent']:.1f}% advantage)"
            )
            print(f"Speed Ratio: {timing['speed_ratio']:.1f}x")
            print(f"Recommendation: {direct['overall_recommendation']}")

    elif args.regression_check:
        # Check for regressions
        print(
            f"🔍 Checking for performance regressions (tolerance: {args.tolerance}%)..."
        )

        regression_history = db.get_regression_history(args.days)

        if not regression_history:
            print("❌ No regression test data found")
            return

        latest_test = regression_history[0]

        print("\n📊 Latest Regression Test:")
        print(f"Status: {'✅ PASSED' if latest_test['passed'] else '❌ FAILED'}")
        print(f"Timestamp: {latest_test['timestamp']}")
        print(f"Regressions: {latest_test['regression_count']}")
        print(f"Improvements: {latest_test['improvement_count']}")

        # Trend analysis
        recent_tests = regression_history[:10]
        pass_rate = (
            sum(1 for test in recent_tests if test["passed"]) / len(recent_tests) * 100
        )

        print("\n📈 Recent Trend (last 10 tests):")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if pass_rate < 70:
            print(
                "🚨 Warning: Low regression test pass rate indicates performance issues"
            )
        elif pass_rate >= 90:
            print(
                "✅ Excellent: High regression test pass rate indicates stable performance"
            )

    else:
        # Default: show database status
        print("📊 Performance Database Status")
        print("=" * 50)

        with sqlite3.connect(db.db_path) as conn:
            # Benchmark count
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT benchmark_name) FROM benchmark_runs"
            )
            benchmark_count = cursor.fetchone()[0]

            # Total runs
            cursor = conn.execute("SELECT COUNT(*) FROM benchmark_runs")
            total_runs = cursor.fetchone()[0]

            # Recent activity
            cursor = conn.execute("""
                SELECT COUNT(*) FROM benchmark_runs
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            recent_runs = cursor.fetchone()[0]

            print(f"Unique Benchmarks: {benchmark_count}")
            print(f"Total Benchmark Runs: {total_runs}")
            print(f"Recent Activity (7 days): {recent_runs}")

            # Show available benchmarks
            cursor = conn.execute("""
                SELECT benchmark_name, language, COUNT(*) as runs,
                       MAX(timestamp) as latest_run
                FROM benchmark_runs
                GROUP BY benchmark_name, language
                ORDER BY latest_run DESC
            """)

            print("\nAvailable Benchmarks:")
            for row in cursor.fetchall():
                print(f"  {row[0]} ({row[1]}): {row[2]} runs, latest: {row[3]}")


if __name__ == "__main__":
    main()

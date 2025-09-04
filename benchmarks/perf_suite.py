#!/usr/bin/env python3
"""
Comprehensive Performance Benchmark Suite for Strataregula

Modular benchmarking framework that provides:
- Individual function/module benchmarking
- Cross-language performance comparison
- Historical performance tracking
- Regression detection
- Customizable test scenarios

Usage:
    python benchmarks/perf_suite.py --module core.compiler
    python benchmarks/perf_suite.py --function expand_patterns --size 10000
    python benchmarks/perf_suite.py --compare --baseline results/baseline.json
    python benchmarks/perf_suite.py --regression-test
"""

import argparse
import gc
import importlib
import json
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any


# Core benchmarking framework
class BenchmarkRunner:
    """Core benchmarking functionality with statistical analysis"""

    def __init__(
        self, warmup_iterations: int = 100, measurement_iterations: int = 1000
    ):
        self.warmup_iterations = warmup_iterations
        self.measurement_iterations = measurement_iterations
        self.results_cache = {}

    def benchmark_function(
        self,
        func: Callable,
        *args,
        name: str | None = None,
        iterations: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Benchmark a single function with comprehensive metrics.

        Returns detailed performance statistics including:
        - Timing percentiles (p50, p95, p99)
        - Memory usage analysis
        - Statistical variance
        - Performance classification
        """
        func_name = name or getattr(func, "__name__", "anonymous_function")
        iterations = iterations or self.measurement_iterations

        # Memory baseline
        gc.collect()
        memory_before = self._get_memory_usage()

        # Warmup phase
        for _ in range(self.warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception as e:
                return {"error": f"Warmup failed: {e!s}", "function": func_name}

        # Measurement phase
        timings = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception as e:
                return {"error": f"Execution failed: {e!s}", "function": func_name}

            timings.append((time.perf_counter() - start) * 1_000_000)  # microseconds

        # Memory measurement
        gc.collect()
        memory_after = self._get_memory_usage()
        memory_delta = memory_after - memory_before

        # Statistical analysis
        timings_sorted = sorted(timings)
        n = len(timings_sorted)

        metrics = {
            "function": func_name,
            "iterations": iterations,
            "timestamp": datetime.now().isoformat(),
            # Timing metrics (microseconds)
            "mean_us": statistics.mean(timings),
            "median_us": timings_sorted[n // 2],
            "p95_us": timings_sorted[int(0.95 * n)],
            "p99_us": timings_sorted[int(0.99 * n)],
            "min_us": min(timings),
            "max_us": max(timings),
            "std_us": statistics.stdev(timings) if n > 1 else 0.0,
            # Throughput
            "ops_per_second": 1_000_000 / statistics.mean(timings),
            # Memory metrics
            "memory_delta_mb": memory_delta / (1024 * 1024),
            "memory_per_op_bytes": memory_delta / iterations if iterations > 0 else 0,
            # Performance classification
            "performance_class": self._classify_performance(statistics.mean(timings)),
            # Variability analysis
            "coefficient_of_variation": (
                statistics.stdev(timings) / statistics.mean(timings)
            )
            if statistics.mean(timings) > 0
            else 0,
        }

        return metrics

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil

            return psutil.Process().memory_info().rss
        except ImportError:
            # Fallback: sum object sizes (less accurate but works)
            return sum(sys.getsizeof(obj) for obj in gc.get_objects())

    def _classify_performance(self, mean_time_us: float) -> str:
        """Classify performance based on timing"""
        if mean_time_us < 1:
            return "excellent"
        elif mean_time_us < 10:
            return "good"
        elif mean_time_us < 100:
            return "acceptable"
        elif mean_time_us < 1000:
            return "slow"
        else:
            return "very_slow"


class ModuleBenchmark:
    """Benchmark entire modules and their key functions"""

    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
        self.module_cache = {}

    def benchmark_module(
        self, module_name: str, test_data: Any = None
    ) -> dict[str, Any]:
        """Benchmark all public functions in a module"""
        try:
            # Import module
            if module_name not in self.module_cache:
                if module_name.startswith("strataregula."):
                    self.module_cache[module_name] = importlib.import_module(
                        module_name
                    )
                else:
                    self.module_cache[module_name] = importlib.import_module(
                        f"strataregula.{module_name}"
                    )

            module = self.module_cache[module_name]

            # Find benchmarkable functions
            functions = self._discover_functions(module)

            # Benchmark each function
            results = {
                "module": module_name,
                "timestamp": datetime.now().isoformat(),
                "functions": {},
            }

            for func_name, func in functions.items():
                print(f"  Benchmarking {module_name}.{func_name}...")

                # Get appropriate test data for function
                test_args, test_kwargs = self._prepare_test_data(func, test_data)

                # Run benchmark
                func_results = self.runner.benchmark_function(
                    func, *test_args, name=f"{module_name}.{func_name}", **test_kwargs
                )

                results["functions"][func_name] = func_results

            return results

        except Exception as e:
            return {"module": module_name, "error": str(e)}

    def _discover_functions(self, module) -> dict[str, Callable]:
        """Discover benchmarkable functions in module"""
        functions = {}

        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)

            # Only benchmark callable functions (not classes)
            if callable(attr) and not isinstance(attr, type):
                functions[attr_name] = attr

        return functions

    def _prepare_test_data(self, func: Callable, provided_data: Any = None) -> tuple:
        """Prepare appropriate test data for function"""
        if provided_data is not None:
            return (provided_data,), {}

        # Analyze function signature for intelligent test data generation
        import inspect

        sig = inspect.signature(func)

        test_args = []
        test_kwargs = {}

        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                # Generate test data based on type annotation
                test_value = self._generate_test_value(param.annotation)
                if param.default == inspect.Parameter.empty:
                    test_args.append(test_value)
                else:
                    test_kwargs[param_name] = test_value

        return tuple(test_args), test_kwargs

    def _generate_test_value(self, annotation) -> Any:
        """Generate appropriate test value for type annotation"""
        if annotation == str:
            return "test_string_value"
        elif annotation == int:
            return 42
        elif annotation == list:
            return list(range(100))
        elif annotation == dict:
            return {f"key_{i}": f"value_{i}" for i in range(50)}
        elif hasattr(annotation, "__origin__"):
            # Handle generic types like List[str], Dict[str, int]
            origin = annotation.__origin__
            if origin == list:
                return list(range(100))
            elif origin == dict:
                return {f"key_{i}": i for i in range(50)}

        # Default fallback
        return None


class ComparisonBenchmark:
    """Compare different implementations of the same functionality"""

    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner

    def compare_implementations(
        self,
        implementations: dict[str, Callable],
        test_data: Any,
        iterations: int | None = None,
    ) -> dict[str, Any]:
        """
        Compare multiple implementations with statistical analysis.

        Args:
            implementations: Dict mapping name to callable
            test_data: Test data to pass to all implementations
            iterations: Number of iterations per implementation

        Returns:
            Detailed comparison report with relative performance metrics
        """
        results = {}

        print(f"Comparing {len(implementations)} implementations...")

        # Benchmark each implementation
        for name, func in implementations.items():
            print(f"  Testing {name}...")
            results[name] = self.runner.benchmark_function(
                func, test_data, name=name, iterations=iterations
            )

        # Calculate relative performance
        self._calculate_relative_metrics(results)

        # Generate comparison report
        comparison_report = {
            "timestamp": datetime.now().isoformat(),
            "test_data_size": self._estimate_data_size(test_data),
            "implementations": results,
            "summary": self._generate_comparison_summary(results),
        }

        return comparison_report

    def _calculate_relative_metrics(self, results: dict[str, dict[str, Any]]) -> None:
        """Add relative performance metrics to results"""
        # Find fastest implementation
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        if not valid_results:
            return

        fastest_name = min(
            valid_results.keys(), key=lambda k: valid_results[k]["mean_us"]
        )
        fastest_time = valid_results[fastest_name]["mean_us"]

        # Calculate relative metrics for all implementations
        for name, metrics in results.items():
            if "error" not in metrics:
                metrics["relative_speed"] = metrics["mean_us"] / fastest_time
                metrics["speedup_factor"] = fastest_time / metrics["mean_us"]
                metrics["is_fastest"] = name == fastest_name

    def _generate_comparison_summary(
        self, results: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate summary statistics for comparison"""
        valid_results = {k: v for k, v in results.items() if "error" not in v}

        if not valid_results:
            return {"error": "No valid results to compare"}

        times = [metrics["mean_us"] for metrics in valid_results.values()]
        fastest = min(valid_results.items(), key=lambda x: x[1]["mean_us"])
        slowest = max(valid_results.items(), key=lambda x: x[1]["mean_us"])

        return {
            "implementations_tested": len(valid_results),
            "fastest_implementation": fastest[0],
            "slowest_implementation": slowest[0],
            "speed_ratio": slowest[1]["mean_us"] / fastest[1]["mean_us"],
            "performance_spread_us": max(times) - min(times),
            "average_performance_us": statistics.mean(times),
            "performance_variance": statistics.variance(times) if len(times) > 1 else 0,
        }

    def _estimate_data_size(self, data: Any) -> str:
        """Estimate test data size for context"""
        try:
            if isinstance(data, list | tuple):
                return f"{len(data)} items"
            elif isinstance(data, dict):
                return f"{len(data)} keys"
            elif isinstance(data, str):
                return f"{len(data)} characters"
            else:
                return f"{sys.getsizeof(data)} bytes"
        except:
            return "unknown size"


class RegressionTester:
    """Automated performance regression testing"""

    def __init__(self, baseline_dir: str = "benchmarks/results"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(exist_ok=True)

    def run_regression_test(
        self, test_suite: dict[str, Callable], tolerance_pct: float = 10.0
    ) -> dict[str, Any]:
        """
        Run performance regression test against stored baseline.

        Args:
            test_suite: Dict of test_name -> test_function
            tolerance_pct: Acceptable performance degradation percentage

        Returns:
            Regression test results with pass/fail status
        """
        runner = BenchmarkRunner()
        current_results = {}

        # Run current benchmarks
        print("Running current performance benchmarks...")
        for test_name, test_func in test_suite.items():
            print(f"  Testing {test_name}...")
            current_results[test_name] = runner.benchmark_function(
                test_func, name=test_name
            )

        # Load baseline results
        baseline_file = self.baseline_dir / "baseline.json"
        baseline_results = self._load_baseline(baseline_file)

        # Compare against baseline
        regression_analysis = self._analyze_regressions(
            current_results, baseline_results, tolerance_pct
        )

        # Save current results as new baseline if no regressions
        if regression_analysis["passed"]:
            self._save_baseline(baseline_file, current_results)

        return {
            "timestamp": datetime.now().isoformat(),
            "current_results": current_results,
            "baseline_results": baseline_results,
            "regression_analysis": regression_analysis,
            "tolerance_pct": tolerance_pct,
        }

    def _load_baseline(self, baseline_file: Path) -> dict[str, Any]:
        """Load baseline performance data"""
        if baseline_file.exists():
            try:
                return json.loads(baseline_file.read_text())
            except Exception as e:
                print(f"Warning: Could not load baseline from {baseline_file}: {e}")

        return {}

    def _save_baseline(self, baseline_file: Path, results: dict[str, Any]) -> None:
        """Save current results as new baseline"""
        # Extract just the performance metrics for baseline
        baseline_data = {}
        for test_name, metrics in results.items():
            if "error" not in metrics:
                baseline_data[test_name] = {
                    "mean_us": metrics["mean_us"],
                    "p95_us": metrics["p95_us"],
                    "ops_per_second": metrics["ops_per_second"],
                    "memory_delta_mb": metrics["memory_delta_mb"],
                }

        baseline_file.write_text(json.dumps(baseline_data, indent=2))
        print(f"[OK] Baseline updated: {baseline_file}")

    def _analyze_regressions(
        self, current: dict[str, Any], baseline: dict[str, Any], tolerance_pct: float
    ) -> dict[str, Any]:
        """Analyze performance regressions"""
        regressions = []
        improvements = []
        tolerance_factor = 1 + (tolerance_pct / 100)

        for test_name, current_metrics in current.items():
            if "error" in current_metrics:
                continue

            if test_name not in baseline:
                continue

            baseline_metrics = baseline[test_name]

            # Check timing regression (higher is worse)
            current_time = current_metrics["mean_us"]
            baseline_time = baseline_metrics["mean_us"]

            if current_time > baseline_time * tolerance_factor:
                degradation_pct = ((current_time - baseline_time) / baseline_time) * 100
                regressions.append(
                    {
                        "test": test_name,
                        "metric": "timing",
                        "baseline_us": baseline_time,
                        "current_us": current_time,
                        "degradation_pct": degradation_pct,
                    }
                )
            elif current_time < baseline_time * 0.9:  # 10% improvement threshold
                improvement_pct = ((baseline_time - current_time) / baseline_time) * 100
                improvements.append(
                    {
                        "test": test_name,
                        "metric": "timing",
                        "baseline_us": baseline_time,
                        "current_us": current_time,
                        "improvement_pct": improvement_pct,
                    }
                )

            # Check memory regression
            current_memory = current_metrics.get("memory_delta_mb", 0)
            baseline_memory = baseline_metrics.get("memory_delta_mb", 0)

            if (
                baseline_memory > 0
                and current_memory > baseline_memory * tolerance_factor
            ):
                memory_degradation = (
                    (current_memory - baseline_memory) / baseline_memory
                ) * 100
                regressions.append(
                    {
                        "test": test_name,
                        "metric": "memory",
                        "baseline_mb": baseline_memory,
                        "current_mb": current_memory,
                        "degradation_pct": memory_degradation,
                    }
                )

        return {
            "passed": len(regressions) == 0,
            "regressions": regressions,
            "improvements": improvements,
            "total_tests": len(current),
            "baseline_tests": len(baseline),
        }


class CrossLanguageBenchmark:
    """Compare performance across Python and PowerShell implementations"""

    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner

    def compare_python_vs_powershell(
        self,
        python_func: Callable,
        powershell_script: str,
        test_data: Any,
        temp_dir: str = "benchmarks/temp",
    ) -> dict[str, Any]:
        """
        Compare Python function vs PowerShell script performance.

        Args:
            python_func: Python function to benchmark
            powershell_script: PowerShell script path or inline code
            test_data: Test data for both implementations
            temp_dir: Temporary directory for data exchange

        Returns:
            Cross-language performance comparison
        """
        temp_path = Path(temp_dir)
        temp_path.mkdir(exist_ok=True)

        # Benchmark Python implementation
        print("Benchmarking Python implementation...")
        python_results = self.runner.benchmark_function(
            python_func, test_data, name="python_implementation"
        )

        # Benchmark PowerShell implementation
        print("Benchmarking PowerShell implementation...")
        powershell_results = self._benchmark_powershell(
            powershell_script, test_data, temp_path
        )

        # Generate comparison
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "python": python_results,
            "powershell": powershell_results,
            "winner": self._determine_winner(python_results, powershell_results),
            "cross_language_analysis": self._analyze_cross_language(
                python_results, powershell_results
            ),
        }

        return comparison

    def _benchmark_powershell(
        self, script_path: str, test_data: Any, temp_dir: Path
    ) -> dict[str, Any]:
        """Benchmark PowerShell script with timing measurement"""

        # Prepare test data file
        data_file = temp_dir / "test_data.json"
        data_file.write_text(json.dumps(test_data, ensure_ascii=False))

        # Create PowerShell benchmark wrapper
        ps_benchmark_script = f'''
        $iterations = {self.runner.measurement_iterations}
        $warmup = {self.runner.warmup_iterations}

        # Load test data
        $testData = Get-Content "{data_file}" | ConvertFrom-Json

        # Warmup
        for ($i = 0; $i -lt $warmup; $i++) {{
            & "{script_path}" -TestData $testData | Out-Null
        }}

        # Measurement
        $times = @()
        for ($i = 0; $i -lt $iterations; $i++) {{
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            & "{script_path}" -TestData $testData | Out-Null
            $sw.Stop()
            $times += $sw.Elapsed.TotalMicroseconds
        }}

        # Statistics
        $sortedTimes = $times | Sort-Object
        $n = $sortedTimes.Count
        $mean = ($times | Measure-Object -Average).Average
        $p95 = $sortedTimes[[math]::Floor(0.95 * $n)]

        @{{
            mean_us = $mean
            p95_us = $p95
            min_us = $sortedTimes[0]
            max_us = $sortedTimes[-1]
            ops_per_second = 1000000 / $mean
            iterations = $iterations
        }} | ConvertTo-Json
        '''

        # Execute PowerShell benchmark
        try:
            result = subprocess.run(
                ["pwsh", "-Command", ps_benchmark_script],
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": f"PowerShell execution failed: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"error": "PowerShell benchmark timed out"}
        except Exception as e:
            return {"error": f"PowerShell benchmark error: {e!s}"}

    def _determine_winner(self, python_results: dict, powershell_results: dict) -> str:
        """Determine which implementation performs better"""
        if "error" in python_results and "error" in powershell_results:
            return "both_failed"
        elif "error" in python_results:
            return "powershell"
        elif "error" in powershell_results:
            return "python"

        python_speed = python_results["ops_per_second"]
        powershell_speed = powershell_results["ops_per_second"]

        if python_speed > powershell_speed * 1.1:  # 10% margin
            return "python"
        elif powershell_speed > python_speed * 1.1:
            return "powershell"
        else:
            return "tie"

    def _analyze_cross_language(
        self, python_results: dict, powershell_results: dict
    ) -> dict[str, Any]:
        """Analyze performance characteristics across languages"""
        if "error" in python_results or "error" in powershell_results:
            return {"analysis": "incomplete_due_to_errors"}

        return {
            "speed_ratio_py_vs_ps": python_results["ops_per_second"]
            / powershell_results["ops_per_second"],
            "python_characteristics": {
                "strength": "computational_operations"
                if python_results["ops_per_second"]
                > powershell_results["ops_per_second"]
                else "memory_efficiency",
                "consistency": "high"
                if python_results["coefficient_of_variation"] < 0.1
                else "moderate",
            },
            "powershell_characteristics": {
                "strength": "system_operations"
                if powershell_results["ops_per_second"]
                > python_results["ops_per_second"]
                else "file_processing",
                "consistency": "high"
                if powershell_results.get("coefficient_of_variation", 0) < 0.1
                else "moderate",
            },
            "recommendation": self._generate_recommendation(
                python_results, powershell_results
            ),
        }

    def _generate_recommendation(
        self, python_results: dict, powershell_results: dict
    ) -> str:
        """Generate implementation recommendation"""
        py_speed = python_results["ops_per_second"]
        ps_speed = powershell_results["ops_per_second"]

        if py_speed > ps_speed * 2:
            return "prefer_python_for_performance"
        elif ps_speed > py_speed * 2:
            return "prefer_powershell_for_performance"
        else:
            return "choose_based_on_context_and_maintainability"


class HistoricalTracker:
    """Track performance metrics over time"""

    def __init__(self, history_dir: str = "benchmarks/history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)

    def record_benchmark(self, benchmark_name: str, results: dict[str, Any]) -> None:
        """Record benchmark results with timestamp"""

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{benchmark_name}_{timestamp}.json"
        result_file = self.history_dir / filename

        # Add metadata
        record = {
            "benchmark_name": benchmark_name,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "system_info": self._get_system_info(),
        }

        result_file.write_text(json.dumps(record, indent=2))

        # Update latest symlink
        latest_file = self.history_dir / f"{benchmark_name}_latest.json"
        if latest_file.exists():
            latest_file.unlink()

        # Create symlink to latest result (Windows compatible)
        try:
            latest_file.write_text(result_file.read_text())
        except Exception:
            pass  # Symlink creation might fail on some systems

    def get_performance_trend(
        self, benchmark_name: str, days: int = 30
    ) -> dict[str, Any]:
        """Analyze performance trends over time"""

        # Find all results for this benchmark
        pattern = f"{benchmark_name}_*.json"
        result_files = list(self.history_dir.glob(pattern))

        if not result_files:
            return {"error": f"No historical data found for {benchmark_name}"}

        # Sort by timestamp and filter by date range
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        recent_results = []

        for file_path in sorted(result_files):
            try:
                data = json.loads(file_path.read_text())
                result_time = datetime.fromisoformat(data["timestamp"]).timestamp()

                if result_time >= cutoff_time:
                    recent_results.append(data)
            except Exception:
                continue

        if not recent_results:
            return {"error": f"No recent data found for {benchmark_name}"}

        # Analyze trends
        return self._analyze_trends(recent_results)

    def _analyze_trends(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance trends from historical data"""

        # Extract timing data
        timing_data = []
        memory_data = []

        for result in results:
            if "results" in result and "mean_us" in result["results"]:
                timing_data.append(
                    {
                        "timestamp": result["timestamp"],
                        "mean_us": result["results"]["mean_us"],
                        "p95_us": result["results"]["p95_us"],
                        "ops_per_second": result["results"]["ops_per_second"],
                    }
                )

                if "memory_delta_mb" in result["results"]:
                    memory_data.append(
                        {
                            "timestamp": result["timestamp"],
                            "memory_mb": result["results"]["memory_delta_mb"],
                        }
                    )

        if not timing_data:
            return {"error": "No valid timing data found"}

        # Calculate trends
        recent_times = [d["mean_us"] for d in timing_data[-5:]]  # Last 5 results
        older_times = (
            [d["mean_us"] for d in timing_data[:-5]] if len(timing_data) > 5 else []
        )

        trend_analysis = {
            "data_points": len(timing_data),
            "time_range_days": self._calculate_time_range(timing_data),
            "performance_stability": self._calculate_stability(recent_times),
            "recent_average_us": statistics.mean(recent_times),
            "overall_trend": self._calculate_trend(timing_data),
        }

        if older_times:
            older_avg = statistics.mean(older_times)
            recent_avg = statistics.mean(recent_times)
            trend_analysis["change_pct"] = ((recent_avg - older_avg) / older_avg) * 100

        return trend_analysis

    def _calculate_stability(self, recent_times: list[float]) -> str:
        """Calculate performance stability rating"""
        if len(recent_times) < 2:
            return "insufficient_data"

        cv = statistics.stdev(recent_times) / statistics.mean(recent_times)

        if cv < 0.05:
            return "very_stable"
        elif cv < 0.1:
            return "stable"
        elif cv < 0.2:
            return "moderate"
        else:
            return "unstable"

    def _calculate_trend(self, timing_data: list[dict]) -> str:
        """Calculate overall performance trend"""
        if len(timing_data) < 3:
            return "insufficient_data"

        # Simple linear trend analysis
        times = [d["mean_us"] for d in timing_data]
        n = len(times)

        # Calculate slope of best fit line
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(times)

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, times, strict=False)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        # Classify trend based on slope
        if abs(slope) < y_mean * 0.001:  # Less than 0.1% change per measurement
            return "stable"
        elif slope > 0:
            return "degrading"
        else:
            return "improving"

    def _calculate_time_range(self, timing_data: list[dict]) -> float:
        """Calculate time range of data in days"""
        if len(timing_data) < 2:
            return 0

        earliest = datetime.fromisoformat(timing_data[0]["timestamp"])
        latest = datetime.fromisoformat(timing_data[-1]["timestamp"])

        return (latest - earliest).total_seconds() / (24 * 3600)

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information for benchmark context"""
        import platform

        info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
        }

        try:
            import psutil

            info["memory_total_gb"] = psutil.virtual_memory().total / (1024**3)
            info["cpu_count"] = psutil.cpu_count()
        except ImportError:
            pass

        return info


# Main CLI interface
def main():
    parser = argparse.ArgumentParser(
        description="Strataregula Performance Benchmark Suite"
    )
    parser.add_argument("--module", help="Module to benchmark (e.g., core.compiler)")
    parser.add_argument("--function", help="Specific function to benchmark")
    parser.add_argument("--size", type=int, default=1000, help="Test data size")
    parser.add_argument("--iterations", type=int, help="Number of benchmark iterations")
    parser.add_argument(
        "--compare", action="store_true", help="Run comparison benchmarks"
    )
    parser.add_argument("--baseline", help="Baseline file for comparison")
    parser.add_argument(
        "--regression-test", action="store_true", help="Run regression test"
    )
    parser.add_argument(
        "--cross-language", action="store_true", help="Compare Python vs PowerShell"
    )
    parser.add_argument(
        "--output", default="benchmarks/results", help="Output directory"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup
    runner = BenchmarkRunner(measurement_iterations=args.iterations or 1000)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    if args.regression_test:
        # Run regression tests
        print("[REGRESSION] Running performance regression tests...")

        # Define core test suite
        test_suite = create_core_test_suite(args.size)

        tester = RegressionTester(str(output_dir))
        regression_results = tester.run_regression_test(test_suite)

        # Save and display results
        result_file = (
            output_dir
            / f"regression_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        result_file.write_text(json.dumps(regression_results, indent=2))

        print_regression_results(regression_results)

        # Exit with appropriate code
        sys.exit(0 if regression_results["regression_analysis"]["passed"] else 1)

    elif args.module:
        # Benchmark specific module
        print(f"[BENCH] Benchmarking module: {args.module}")

        module_benchmark = ModuleBenchmark(runner)
        results = module_benchmark.benchmark_module(args.module)

        # Save results
        result_file = (
            output_dir
            / f"module_{args.module.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        result_file.write_text(json.dumps(results, indent=2))

        print_module_results(results)

    elif args.compare:
        # Run comparison benchmarks
        print("[COMPARE] Running implementation comparisons...")

        # Example: Compare different pattern expansion implementations
        implementations = create_comparison_implementations()
        test_data = create_test_data(args.size)

        comparator = ComparisonBenchmark(runner)
        comparison_results = comparator.compare_implementations(
            implementations, test_data
        )

        # Save results
        result_file = (
            output_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        result_file.write_text(json.dumps(comparison_results, indent=2))

        print_comparison_results(comparison_results)

    else:
        # Default: run comprehensive benchmark suite
        print("[PERF] Running comprehensive performance benchmark suite...")
        run_comprehensive_benchmark(runner, args.size, output_dir)


def create_core_test_suite(data_size: int) -> dict[str, Callable]:
    """Create core test suite for regression testing"""

    def test_pattern_compilation():
        """Test pattern compilation performance"""
        from strataregula.core.compiler import PatternCompiler

        compiler = PatternCompiler()
        patterns = {f"service.{i}.config": f"value_{i}" for i in range(data_size)}
        return list(compiler.compile_patterns(patterns))

    def test_pattern_expansion():
        """Test pattern expansion performance"""
        from strataregula.core.pattern_expander import PatternExpander

        expander = PatternExpander()
        patterns = {
            f"region.{i}.service.*": f"config_{i}" for i in range(data_size // 10)
        }
        return list(expander.expand_pattern_stream(patterns))

    def test_json_processing():
        """Test JSON processing performance"""
        from strataregula.json_processor.commands import JsonProcessor

        processor = JsonProcessor()
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(data_size)]}
        return processor.process(data)

    def test_index_search():
        """Test index search performance"""
        from strataregula.index.content_search import ContentSearch

        search = ContentSearch()
        # Simulate search operation
        content = {
            f"doc_{i}": f"content for document {i}" for i in range(data_size // 100)
        }
        return search.search_content(content, "document")

    return {
        "pattern_compilation": test_pattern_compilation,
        "pattern_expansion": test_pattern_expansion,
        "json_processing": test_json_processing,
        "index_search": test_index_search,
    }


def create_comparison_implementations() -> dict[str, Callable]:
    """Create implementations for comparison testing"""

    # Example: Different approaches to pattern matching
    def naive_pattern_match(patterns, target):
        """Naive pattern matching implementation"""
        return any(pattern == target for pattern in patterns)

    def optimized_pattern_match(patterns, target):
        """Optimized pattern matching with set lookup"""
        pattern_set = set(patterns)
        return target in pattern_set

    def regex_pattern_match(patterns, target):
        """Regex-based pattern matching"""
        import re

        combined_pattern = "|".join(re.escape(p) for p in patterns)
        regex = re.compile(combined_pattern)
        return regex.match(target) is not None

    return {
        "naive_implementation": naive_pattern_match,
        "optimized_implementation": optimized_pattern_match,
        "regex_implementation": regex_pattern_match,
    }


def create_test_data(size: int) -> Any:
    """Create test data of specified size"""
    return [f"pattern_{i}" for i in range(size)]


def print_regression_results(results: dict[str, Any]) -> None:
    """Print formatted regression test results"""
    analysis = results["regression_analysis"]

    print("\n" + "=" * 60)
    print("PERFORMANCE REGRESSION TEST RESULTS")
    print("=" * 60)

    if analysis["passed"]:
        print("[PASS] PASSED: No performance regressions detected")
    else:
        print("[FAIL] FAILED: Performance regressions detected")

    print(f"\nTests run: {analysis['total_tests']}")
    print(f"Baseline tests: {analysis['baseline_tests']}")

    if analysis["regressions"]:
        print(f"[FAIL] Regressions ({len(analysis['regressions'])}):")
        for reg in analysis["regressions"]:
            print(
                f"  {reg['test']} ({reg['metric']}): {reg['degradation_pct']:.1f}% slower"
            )

    if analysis["improvements"]:
        print(f"[IMPROVE] Improvements ({len(analysis['improvements'])}):")
        for imp in analysis["improvements"]:
            print(
                f"  {imp['test']} ({imp['metric']}): {imp['improvement_pct']:.1f}% faster"
            )


def print_module_results(results: dict[str, Any]) -> None:
    """Print formatted module benchmark results"""
    print("\n" + "=" * 60)
    print(f"MODULE BENCHMARK: {results.get('module', 'unknown')}")
    print("=" * 60)

    if "error" in results:
        print(f"[ERROR] Error: {results['error']}")
        return

    functions = results.get("functions", {})
    if not functions:
        print("No functions found to benchmark")
        return

    print(
        f"{'Function':<25} {'Mean (μs)':<12} {'P95 (μs)':<12} {'Ops/sec':<12} {'Class'}"
    )
    print("-" * 80)

    for func_name, metrics in functions.items():
        if "error" not in metrics:
            print(
                f"{func_name:<25} {metrics['mean_us']:<12.2f} {metrics['p95_us']:<12.2f} "
                f"{metrics['ops_per_second']:<12.0f} {metrics['performance_class']}"
            )
        else:
            print(f"{func_name:<25} ERROR: {metrics['error']}")


def print_comparison_results(results: dict[str, Any]) -> None:
    """Print formatted comparison results"""
    print("\n" + "=" * 60)
    print("IMPLEMENTATION COMPARISON RESULTS")
    print("=" * 60)

    implementations = results.get("implementations", {})
    summary = results.get("summary", {})

    print(f"{'Implementation':<20} {'Mean (μs)':<12} {'Relative':<10} {'Status'}")
    print("-" * 60)

    for name, metrics in implementations.items():
        if "error" not in metrics:
            status = (
                "[FAST]"
                if metrics.get("is_fastest")
                else "[GOOD]"
                if metrics["relative_speed"] < 2
                else "[SLOW]"
            )
            print(
                f"{name:<20} {metrics['mean_us']:<12.2f} {metrics['relative_speed']:<10.1f}x {status}"
            )
        else:
            print(f"{name:<20} ERROR: {metrics['error']}")

    if summary and "fastest_implementation" in summary:
        print(f"\n🏆 Winner: {summary['fastest_implementation']}")
        print(f"[STATS] Speed ratio: {summary['speed_ratio']:.1f}x")


def run_comprehensive_benchmark(
    runner: BenchmarkRunner, data_size: int, output_dir: Path
) -> None:
    """Run comprehensive benchmark suite"""

    print("[START] Starting comprehensive performance benchmark...")

    # 1. Core functionality benchmarks
    print("\n1. Core Functionality Benchmarks")
    test_suite = create_core_test_suite(data_size)
    core_results = {}

    for test_name, test_func in test_suite.items():
        print(f"   Testing {test_name}...")
        core_results[test_name] = runner.benchmark_function(test_func, name=test_name)

    # 2. Implementation comparisons
    print("\n2. Implementation Comparisons")
    implementations = create_comparison_implementations()
    test_data = create_test_data(100)  # Smaller data for comparison

    comparator = ComparisonBenchmark(runner)
    comparison_results = comparator.compare_implementations(implementations, test_data)

    # 3. Save comprehensive results
    comprehensive_results = {
        "timestamp": datetime.now().isoformat(),
        "data_size": data_size,
        "core_benchmarks": core_results,
        "implementation_comparisons": comparison_results,
        "system_info": HistoricalTracker()._get_system_info(),
    }

    # Save to file
    result_file = (
        output_dir / f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    result_file.write_text(json.dumps(comprehensive_results, indent=2))

    print(f"[SAVED] Results saved to: {result_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE BENCHMARK SUMMARY")
    print("=" * 60)

    print("\nCore Function Performance:")
    for name, metrics in core_results.items():
        if "error" not in metrics:
            print(
                f"  {name}: {metrics['ops_per_second']:.0f} ops/sec ({metrics['performance_class']})"
            )
        else:
            print(f"  {name}: ERROR - {metrics['error']}")

    print(
        f"\nImplementation Comparison Winner: {comparison_results['summary']['fastest_implementation']}"
    )
    print(f"Performance spread: {comparison_results['summary']['speed_ratio']:.1f}x")


if __name__ == "__main__":
    main()

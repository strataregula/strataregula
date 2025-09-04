#!/usr/bin/env python3
"""
Performance Benchmark Template for Strataregula Components

This template provides a standardized approach for creating performance benchmarks
for new components, functions, or optimization efforts in Strataregula.

Usage:
1. Copy this template
2. Customize the test functions and data generation
3. Run benchmark: python your_benchmark.py
4. Results will be automatically integrated into the performance tracking system

Template Sections:
- Function benchmarking
- Module benchmarking
- Comparison benchmarking
- Regression testing integration
- Performance requirements validation
"""

import json
import statistics
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.perf_suite import BenchmarkRunner, ComparisonBenchmark, RegressionTester
from tools.perf_reporter import PerformanceDatabase


class CustomBenchmark:
    """
    Custom benchmark template class.

    Customize this class for your specific benchmarking needs:
    1. Modify test_functions to include your functions
    2. Update create_test_data for realistic test scenarios
    3. Adjust performance_requirements for your component
    4. Add custom analysis logic if needed
    """

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.runner = BenchmarkRunner(
            warmup_iterations=100, measurement_iterations=1000
        )
        self.results = {}

        # Performance requirements for this component
        self.performance_requirements = {
            "max_time_us": 1000,  # Maximum 1ms per operation
            "min_throughput_ops": 1000,  # Minimum 1000 operations per second
            "max_memory_mb": 50,  # Maximum 50MB memory usage
            "max_p95_us": 2000,  # 95th percentile under 2ms
        }

    def create_test_data(self, scenario: str = "typical") -> Any:
        """
        Create test data for benchmarking.

        Customize this method to generate realistic test data for your component.
        Consider different scenarios: minimal, typical, production, stress.
        """
        scenarios = {
            "minimal": {"size": 100, "complexity": 1},
            "typical": {"size": 1000, "complexity": 3},
            "production": {"size": 10000, "complexity": 5},
            "stress": {"size": 100000, "complexity": 10},
        }

        config = scenarios.get(scenario, scenarios["typical"])

        # Example: Generate test patterns (customize for your data type)
        test_data = {}
        for i in range(config["size"]):
            # Create data with specified complexity
            key_parts = [f"level{j}" for j in range(config["complexity"])]
            if i % 10 == 0:  # Add some wildcards
                key_parts[config["complexity"] // 2] = "*"

            key = ".".join(key_parts) + f".item{i}"
            test_data[key] = f"value_{i}_{scenario}"

        return test_data

    def define_test_functions(self) -> dict[str, Callable]:
        """
        Define functions to benchmark.

        Customize this method to include your specific functions.
        Each function should:
        1. Take test_data as parameter
        2. Return a measurable result
        3. Be representative of real usage
        """

        # Example test functions - replace with your actual functions
        def test_function_1(test_data):
            """Example: Test basic processing function"""
            # Replace with your actual function
            result = []
            for key, value in test_data.items():
                if "*" not in key:  # Simple processing
                    result.append(f"{key}={value}")
            return len(result)

        def test_function_2(test_data):
            """Example: Test pattern matching function"""
            # Replace with your actual pattern matching logic
            patterns = [key for key in test_data if "*" in key]
            matches = 0

            for pattern in patterns:
                for key in test_data:
                    if self._simple_match(pattern, key):
                        matches += 1

            return matches

        def test_function_3(test_data):
            """Example: Test data transformation function"""
            # Replace with your actual transformation logic
            transformed = {}
            for key, value in test_data.items():
                new_key = key.replace("*", "wildcard")
                transformed[new_key] = value.upper()

            return len(transformed)

        return {
            "basic_processing": test_function_1,
            "pattern_matching": test_function_2,
            "data_transformation": test_function_3,
        }

    def _simple_match(self, pattern: str, target: str) -> bool:
        """Simple pattern matching for example (replace with actual logic)"""
        import fnmatch

        return fnmatch.fnmatch(target, pattern)

    def run_individual_benchmarks(self, test_data: Any) -> dict[str, Any]:
        """Run benchmarks for individual functions"""

        test_functions = self.define_test_functions()
        individual_results = {}

        print(f"🔧 Running individual function benchmarks for {self.component_name}...")

        for func_name, func in test_functions.items():
            print(f"  Benchmarking {func_name}...")

            # Run benchmark
            result = self.runner.benchmark_function(
                func, test_data, name=f"{self.component_name}.{func_name}"
            )

            individual_results[func_name] = result

            # Validate against requirements
            validation = self._validate_requirements(result)
            result["validation"] = validation

            # Display result
            self._display_function_result(func_name, result, validation)

        return individual_results

    def run_comparison_benchmark(self, test_data: Any) -> dict[str, Any]:
        """
        Run comparison between different implementations.

        Customize this method to compare your implementations:
        - Different algorithms
        - Optimized vs unoptimized versions
        - Different approaches to same problem
        """

        # Example implementations - replace with your actual implementations
        implementations = {
            "naive_implementation": lambda data: self._naive_approach(data),
            "optimized_implementation": lambda data: self._optimized_approach(data),
            "alternative_implementation": lambda data: self._alternative_approach(data),
        }

        print(f"⚖️ Running comparison benchmarks for {self.component_name}...")

        comparator = ComparisonBenchmark(self.runner)
        comparison_results = comparator.compare_implementations(
            implementations, test_data
        )

        # Display comparison results
        self._display_comparison_results(comparison_results)

        return comparison_results

    def _naive_approach(self, test_data: Any) -> Any:
        """
        Naive implementation for comparison.
        Replace with your actual naive implementation.
        """
        # Example: Simple linear processing
        results = []
        for key, value in test_data.items():
            processed = f"{key.upper()}={value.lower()}"
            results.append(processed)
        return results

    def _optimized_approach(self, test_data: Any) -> Any:
        """
        Optimized implementation for comparison.
        Replace with your actual optimized implementation.
        """
        # Example: Optimized processing with list comprehension
        return [f"{key.upper()}={value.lower()}" for key, value in test_data.items()]

    def _alternative_approach(self, test_data: Any) -> Any:
        """
        Alternative implementation for comparison.
        Replace with your actual alternative implementation.
        """

        # Example: Generator-based approach for memory efficiency
        def generate_results():
            for key, value in test_data.items():
                yield f"{key.upper()}={value.lower()}"

        return list(generate_results())

    def run_scalability_test(self) -> dict[str, Any]:
        """Test scalability across different data sizes"""

        print(f"📊 Running scalability tests for {self.component_name}...")

        test_functions = self.define_test_functions()
        primary_function = next(
            iter(test_functions.values())
        )  # Use first function for scalability

        scalability_results = {}
        sizes = [100, 500, 1000, 5000, 10000]

        for size in sizes:
            print(f"  Testing with size {size:,}...")

            # Create data of specific size
            test_data = self.create_test_data("minimal")
            sized_data = dict(list(test_data.items())[:size])

            try:
                # Measure performance at this size
                result = self.runner.benchmark_function(
                    primary_function,
                    sized_data,
                    name=f"{self.component_name}_size_{size}",
                )

                scalability_results[size] = {
                    "success": True,
                    "duration_us": result["mean_us"],
                    "throughput_ops_per_sec": result["ops_per_second"],
                    "memory_mb": result.get("memory_delta_mb", 0),
                    "items_processed": len(sized_data),
                }

            except Exception as e:
                scalability_results[size] = {"success": False, "error": str(e)}
                break  # Stop testing larger sizes if one fails

        # Analyze scalability characteristics
        analysis = self._analyze_scalability(scalability_results)

        return {
            "scalability_results": scalability_results,
            "scalability_analysis": analysis,
        }

    def _analyze_scalability(self, results: dict[int, Any]) -> dict[str, Any]:
        """Analyze scalability characteristics"""

        successful_results = {k: v for k, v in results.items() if v.get("success")}

        if len(successful_results) < 2:
            return {"error": "Insufficient data for scalability analysis"}

        # Calculate scaling efficiency
        sizes = sorted(successful_results.keys())
        throughputs = [
            successful_results[size]["throughput_ops_per_sec"] for size in sizes
        ]

        # Ideal linear scaling would maintain constant throughput
        throughput_variance = (
            statistics.variance(throughputs) if len(throughputs) > 1 else 0
        )
        avg_throughput = statistics.mean(throughputs)

        # Memory scaling analysis
        memory_usage = [successful_results[size]["memory_mb"] for size in sizes]
        memory_per_item = [
            memory / size for memory, size in zip(memory_usage, sizes, strict=False)
        ]

        return {
            "max_successful_size": max(sizes),
            "throughput_variance": throughput_variance,
            "average_throughput": avg_throughput,
            "scaling_efficiency": "linear"
            if throughput_variance < avg_throughput * 0.1
            else "sublinear",
            "memory_scaling": {
                "per_item_mb": statistics.mean(memory_per_item),
                "scaling_pattern": self._classify_memory_scaling(memory_per_item),
            },
            "performance_limit_reached": len(successful_results) < len(results),
        }

    def _classify_memory_scaling(self, memory_per_item: list[float]) -> str:
        """Classify memory scaling pattern"""

        if len(memory_per_item) < 2:
            return "insufficient_data"

        # Check if memory per item increases (bad) or stays constant (good)
        first_half_avg = statistics.mean(memory_per_item[: len(memory_per_item) // 2])
        second_half_avg = statistics.mean(memory_per_item[len(memory_per_item) // 2 :])

        if second_half_avg > first_half_avg * 1.2:
            return "degrading"  # Memory usage growing faster than data
        elif second_half_avg < first_half_avg * 0.8:
            return "improving"  # Getting more memory efficient with scale
        else:
            return "constant"  # Linear memory scaling

    def run_regression_integration(self) -> dict[str, Any]:
        """Integrate with regression testing system"""

        print(f"🔍 Running regression test integration for {self.component_name}...")

        # Run benchmarks with test data
        test_data = self.create_test_data("typical")
        current_results = self.run_individual_benchmarks(test_data)

        # Store in performance database
        db = PerformanceDatabase()

        # Format for database storage
        formatted_results = {"functions": current_results}
        db.store_benchmark_results(self.component_name, "python", formatted_results)

        # Check for regressions against historical data
        tester = RegressionTester("benchmarks/results")

        # Create test suite for regression testing
        test_functions = self.define_test_functions()
        regression_results = tester.run_regression_test(
            test_functions, tolerance_pct=10.0
        )

        return {
            "current_benchmark_results": current_results,
            "regression_test_results": regression_results,
            "database_storage": "completed",
            "recommendations": self._generate_recommendations(
                current_results, regression_results
            ),
        }

    def _validate_requirements(self, result: dict[str, Any]) -> dict[str, Any]:
        """Validate benchmark result against performance requirements"""

        violations = []
        warnings = []

        # Check timing requirement
        if result.get("mean_us", 0) > self.performance_requirements["max_time_us"]:
            violations.append(
                {
                    "metric": "timing",
                    "requirement": f"<{self.performance_requirements['max_time_us']}μs",
                    "actual": f"{result['mean_us']:.1f}μs",
                    "severity": "high",
                }
            )
        elif (
            result.get("mean_us", 0)
            > self.performance_requirements["max_time_us"] * 0.8
        ):
            warnings.append(
                {
                    "metric": "timing",
                    "message": f"Approaching timing limit: {result['mean_us']:.1f}μs",
                    "limit": self.performance_requirements["max_time_us"],
                }
            )

        # Check throughput requirement
        if (
            result.get("ops_per_second", 0)
            < self.performance_requirements["min_throughput_ops"]
        ):
            violations.append(
                {
                    "metric": "throughput",
                    "requirement": f">{self.performance_requirements['min_throughput_ops']} ops/sec",
                    "actual": f"{result['ops_per_second']:.0f} ops/sec",
                    "severity": "medium",
                }
            )

        # Check memory requirement
        if (
            result.get("memory_delta_mb", 0)
            > self.performance_requirements["max_memory_mb"]
        ):
            violations.append(
                {
                    "metric": "memory",
                    "requirement": f"<{self.performance_requirements['max_memory_mb']}MB",
                    "actual": f"{result['memory_delta_mb']:.1f}MB",
                    "severity": "medium",
                }
            )

        # Check p95 requirement
        if result.get("p95_us", 0) > self.performance_requirements["max_p95_us"]:
            violations.append(
                {
                    "metric": "latency_p95",
                    "requirement": f"<{self.performance_requirements['max_p95_us']}μs",
                    "actual": f"{result['p95_us']:.1f}μs",
                    "severity": "high",
                }
            )

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "overall_score": self._calculate_performance_score(result),
        }

    def _calculate_performance_score(self, result: dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""

        scores = []

        # Timing score (0-100, where meeting requirement = 100)
        timing_ratio = (
            result.get("mean_us", 0) / self.performance_requirements["max_time_us"]
        )
        timing_score = (
            max(0, 100 - (timing_ratio - 1) * 100) if timing_ratio > 1 else 100
        )
        scores.append(timing_score)

        # Throughput score
        throughput_ratio = (
            result.get("ops_per_second", 0)
            / self.performance_requirements["min_throughput_ops"]
        )
        throughput_score = min(100, throughput_ratio * 100)
        scores.append(throughput_score)

        # Memory score
        memory_ratio = (
            result.get("memory_delta_mb", 0)
            / self.performance_requirements["max_memory_mb"]
        )
        memory_score = (
            max(0, 100 - (memory_ratio - 1) * 100) if memory_ratio > 1 else 100
        )
        scores.append(memory_score)

        return statistics.mean(scores)

    def _display_function_result(
        self, func_name: str, result: dict[str, Any], validation: dict[str, Any]
    ) -> None:
        """Display benchmark result for individual function"""

        status_icon = "✅" if validation["passed"] else "❌"
        print(f"    {status_icon} {func_name}:")
        print(f"      Time: {result['mean_us']:.2f}μs (p95: {result['p95_us']:.2f}μs)")
        print(f"      Throughput: {result['ops_per_second']:.0f} ops/sec")
        print(f"      Memory: {result.get('memory_delta_mb', 0):.2f}MB")
        print(f"      Score: {validation['overall_score']:.1f}/100")

        if validation["violations"]:
            for violation in validation["violations"]:
                print(
                    f"      🚨 {violation['metric'].upper()}: {violation['actual']} (req: {violation['requirement']})"
                )

        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"      ⚠️ {warning['message']}")

    def _display_comparison_results(self, results: dict[str, Any]) -> None:
        """Display comparison benchmark results"""

        implementations = results.get("implementations", {})
        summary = results.get("summary", {})

        print("\n⚖️ Implementation Comparison Results:")
        print(f"{'Implementation':<25} {'Mean (μs)':<12} {'Relative':<10} {'Status'}")
        print("-" * 65)

        for name, metrics in implementations.items():
            if "error" not in metrics:
                status = (
                    "🏆"
                    if metrics.get("is_fastest")
                    else "✅"
                    if metrics["relative_speed"] < 2
                    else "⚠️"
                )
                print(
                    f"{name:<25} {metrics['mean_us']:<12.2f} {metrics['relative_speed']:<10.1f}x {status}"
                )
            else:
                print(f"{name:<25} ERROR: {metrics['error']}")

        if summary:
            print(f"\n🏆 Winner: {summary.get('fastest_implementation', 'unknown')}")
            print(f"📊 Speed ratio: {summary.get('speed_ratio', 0):.1f}x")

    def _generate_recommendations(
        self, current_results: dict, regression_results: dict
    ) -> list[str]:
        """Generate recommendations based on benchmark results"""

        recommendations = []

        # Analyze current performance
        failed_validations = [
            name
            for name, result in current_results.items()
            if not result.get("validation", {}).get("passed", True)
        ]

        if failed_validations:
            recommendations.append(
                f"🚨 PERFORMANCE: Optimize functions failing requirements: {', '.join(failed_validations)}"
            )

        # Analyze regression results
        if regression_results.get("regression_analysis", {}).get("regressions"):
            regressions = regression_results["regression_analysis"]["regressions"]
            regression_tests = [r["test"] for r in regressions]
            recommendations.append(
                f"📉 REGRESSION: Address performance regressions in: {', '.join(regression_tests)}"
            )

        # Performance score analysis
        scores = [
            result.get("validation", {}).get("overall_score", 0)
            for result in current_results.values()
        ]
        avg_score = statistics.mean(scores) if scores else 0

        if avg_score < 70:
            recommendations.append(
                "⚡ OPTIMIZATION: Overall performance score below 70 - consider algorithmic improvements"
            )
        elif avg_score < 85:
            recommendations.append(
                "📈 IMPROVEMENT: Good performance but room for optimization"
            )

        # Memory efficiency analysis
        memory_usage = [
            result.get("memory_delta_mb", 0) for result in current_results.values()
        ]
        total_memory = sum(memory_usage)

        if total_memory > 100:
            recommendations.append(
                "💾 MEMORY: High memory usage detected - consider memory optimization patterns"
            )

        if not recommendations:
            recommendations.append(
                "✅ EXCELLENT: All performance metrics within acceptable ranges"
            )

        return recommendations

    def run_comprehensive_benchmark(self) -> dict[str, Any]:
        """Run complete benchmark suite"""

        print(f"🚀 Starting comprehensive benchmark for {self.component_name}")
        print("=" * 60)

        # 1. Create test data
        test_data = self.create_test_data("typical")
        print(
            f"📊 Test data: {len(test_data) if hasattr(test_data, '__len__') else 'streaming'} items"
        )

        # 2. Individual function benchmarks
        individual_results = self.run_individual_benchmarks(test_data)

        # 3. Implementation comparison
        comparison_results = self.run_comparison_benchmark(test_data)

        # 4. Scalability testing
        scalability_results = self.run_scalability_test()

        # 5. Regression testing integration
        regression_integration = self.run_regression_integration()

        # 6. Compile comprehensive report
        comprehensive_report = {
            "component_name": self.component_name,
            "timestamp": datetime.now().isoformat(),
            "test_configuration": {
                "warmup_iterations": self.runner.warmup_iterations,
                "measurement_iterations": self.runner.measurement_iterations,
                "performance_requirements": self.performance_requirements,
            },
            "individual_benchmarks": individual_results,
            "comparison_benchmarks": comparison_results,
            "scalability_tests": scalability_results,
            "regression_integration": regression_integration,
            "overall_assessment": self._generate_overall_assessment(
                individual_results, comparison_results, scalability_results
            ),
        }

        # 7. Save results
        self._save_comprehensive_results(comprehensive_report)

        # 8. Display summary
        self._display_comprehensive_summary(comprehensive_report)

        return comprehensive_report

    def _generate_overall_assessment(
        self, individual: dict, comparison: dict, scalability: dict
    ) -> dict[str, Any]:
        """Generate overall assessment of component performance"""

        # Calculate overall scores
        individual_scores = [
            result.get("validation", {}).get("overall_score", 0)
            for result in individual.values()
        ]

        avg_individual_score = (
            statistics.mean(individual_scores) if individual_scores else 0
        )

        # Scalability assessment
        scalability_analysis = scalability.get("scalability_analysis", {})
        scalability_rating = (
            "good"
            if scalability_analysis.get("scaling_efficiency") == "linear"
            else "needs_improvement"
        )

        # Comparison assessment
        comparison_summary = comparison.get("summary", {})
        fastest_impl = comparison_summary.get("fastest_implementation", "unknown")

        # Overall health rating
        if avg_individual_score >= 90 and scalability_rating == "good":
            health_rating = "excellent"
        elif avg_individual_score >= 75:
            health_rating = "good"
        elif avg_individual_score >= 60:
            health_rating = "acceptable"
        else:
            health_rating = "needs_optimization"

        return {
            "overall_score": avg_individual_score,
            "health_rating": health_rating,
            "scalability_rating": scalability_rating,
            "recommended_implementation": fastest_impl,
            "ready_for_production": health_rating in ["excellent", "good"],
            "optimization_priority": "high"
            if health_rating == "needs_optimization"
            else "medium"
            if health_rating == "acceptable"
            else "low",
        }

    def _save_comprehensive_results(self, report: dict[str, Any]) -> None:
        """Save comprehensive benchmark results"""

        # Save to results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(
            f"benchmarks/results/{self.component_name}_comprehensive_{timestamp}.json"
        )
        result_file.parent.mkdir(exist_ok=True)

        result_file.write_text(json.dumps(report, indent=2))
        print(f"📁 Results saved to: {result_file}")

        # Update latest results symlink
        latest_file = Path(f"benchmarks/results/{self.component_name}_latest.json")
        try:
            if latest_file.exists():
                latest_file.unlink()
            latest_file.write_text(result_file.read_text())
        except Exception:
            pass  # Symlink creation might fail on some systems

    def _display_comprehensive_summary(self, report: dict[str, Any]) -> None:
        """Display comprehensive benchmark summary"""

        assessment = report["overall_assessment"]

        print("\n" + "=" * 60)
        print(f"COMPREHENSIVE BENCHMARK SUMMARY: {self.component_name.upper()}")
        print("=" * 60)

        print(f"Overall Score: {assessment['overall_score']:.1f}/100")
        print(f"Health Rating: {assessment['health_rating'].upper()}")
        print(f"Scalability: {assessment['scalability_rating'].upper()}")
        print(f"Recommended Implementation: {assessment['recommended_implementation']}")
        print(
            f"Production Ready: {'YES' if assessment['ready_for_production'] else 'NO'}"
        )
        print(f"Optimization Priority: {assessment['optimization_priority'].upper()}")

        # Show recommendations
        recommendations = report["regression_integration"]["recommendations"]
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")

        print("\n📊 Detailed results saved to benchmarks/results/")


# Example usage and customization
def create_custom_benchmark_example():
    """Example of how to customize the benchmark template"""

    class MyComponentBenchmark(CustomBenchmark):
        """Custom benchmark for your specific component"""

        def __init__(self):
            super().__init__("my_component")

            # Customize performance requirements
            self.performance_requirements = {
                "max_time_us": 500,  # Your component's timing requirement
                "min_throughput_ops": 2000,  # Your throughput requirement
                "max_memory_mb": 25,  # Your memory requirement
                "max_p95_us": 1000,  # Your latency requirement
            }

        def create_test_data(self, scenario: str = "typical") -> Any:
            """Create test data specific to your component"""

            # Replace with your component's data structure
            if scenario == "minimal":
                return {"simple_key": "simple_value"}
            elif scenario == "typical":
                return {f"key_{i}": f"value_{i}" for i in range(1000)}
            elif scenario == "production":
                return {
                    f"complex.key.{i}.{j}": f"complex_value_{i}_{j}"
                    for i in range(100)
                    for j in range(50)
                }
            else:
                return self.create_test_data("typical")

        def define_test_functions(self) -> dict[str, Callable]:
            """Define your component's functions to benchmark"""

            def my_core_function(test_data):
                # Replace with your actual function
                return len([k for k in test_data if "." in k])

            def my_optimization_function(test_data):
                # Replace with your optimized version
                return sum(1 for k in test_data if "." in k)

            return {
                "core_function": my_core_function,
                "optimized_function": my_optimization_function,
            }

    # Run custom benchmark
    benchmark = MyComponentBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    return results


# Main execution for template usage
def main():
    """Main function for running template benchmark"""

    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmark Template")
    parser.add_argument(
        "--component", required=True, help="Component name to benchmark"
    )
    parser.add_argument(
        "--scenario",
        default="typical",
        choices=["minimal", "typical", "production", "stress"],
        help="Test data scenario",
    )
    parser.add_argument(
        "--test-type",
        default="comprehensive",
        choices=["individual", "comparison", "scalability", "comprehensive"],
        help="Type of benchmark to run",
    )
    parser.add_argument("--iterations", type=int, help="Number of benchmark iterations")

    args = parser.parse_args()

    # Create benchmark instance
    benchmark = CustomBenchmark(args.component)

    # Override iterations if specified
    if args.iterations:
        benchmark.runner.measurement_iterations = args.iterations

    # Create test data
    test_data = benchmark.create_test_data(args.scenario)

    # Run specified benchmark type
    if args.test_type == "individual":
        benchmark.run_individual_benchmarks(test_data)

    elif args.test_type == "comparison":
        benchmark.run_comparison_benchmark(test_data)

    elif args.test_type == "scalability":
        benchmark.run_scalability_test()

    else:  # comprehensive
        benchmark.run_comprehensive_benchmark()

    print(f"\n✅ Benchmark completed for {args.component}")


if __name__ == "__main__":
    main()

# Quick start examples for common use cases

# Example 1: Benchmark a new function
"""
from benchmark_template import CustomBenchmark

def my_new_function(data):
    # Your function implementation
    return processed_data

# Create benchmark
benchmark = CustomBenchmark("my_new_function")

# Override test functions
benchmark.define_test_functions = lambda: {'my_function': my_new_function}

# Run benchmark
test_data = benchmark.create_test_data('typical')
results = benchmark.run_individual_benchmarks(test_data)
"""

# Example 2: Compare implementations
"""
benchmark = CustomBenchmark("implementation_comparison")

implementations = {
    'current': current_implementation,
    'optimized': optimized_implementation,
    'alternative': alternative_implementation
}

comparator = ComparisonBenchmark(benchmark.runner)
comparison_results = comparator.compare_implementations(implementations, test_data)
"""

# Example 3: Add to regression testing
"""
def integrate_with_regression_testing():
    benchmark = CustomBenchmark("my_component")

    # Define test suite
    test_suite = {
        'my_function': lambda: my_function(test_data),
        'my_other_function': lambda: my_other_function(test_data)
    }

    # Run regression test
    tester = RegressionTester("benchmarks/results")
    regression_results = tester.run_regression_test(test_suite)

    return regression_results
"""

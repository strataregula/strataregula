"""Profiling setup for yaml-config-compiler performance analysis."""

import sys
import time
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, Any, List, Callable
import psutil
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from yaml_config_compiler import YAMLCompiler, WildcardExpander


class PerformanceProfiler:
    """Performance profiling and analysis tools."""
    
    def __init__(self):
        self.results = {}
        self.memory_usage = []
        
    def profile_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Profile a function execution."""
        # Memory before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Profile execution
        profiler = cProfile.Profile()
        start_time = time.perf_counter()
        
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        end_time = time.perf_counter()
        
        # Memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Get profile stats
        stats_stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats('cumulative').print_stats(20)
        
        return {
            'execution_time': end_time - start_time,
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_increase_mb': memory_after - memory_before,
            'profile_stats': stats_stream.getvalue(),
            'result': result
        }
    
    def benchmark_pattern_expansion(self, patterns: List[str], iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark pattern expansion with current implementation."""
        print(f"Benchmarking {len(patterns)} patterns, {iterations} iterations...")
        
        # Create compiler
        compiler = YAMLCompiler()
        compiler.set_regions(['us-east', 'us-west', 'eu-central'])
        compiler.set_prefectures(['tokyo', 'osaka', 'kyoto'])
        
        def run_expansions():
            results = []
            for _ in range(iterations):
                for pattern in patterns:
                    expanded = compiler.expander.expand_pattern(pattern, 0.05)
                    results.append(len(expanded))
            return results
        
        return self.profile_function(run_expansions)
    
    def benchmark_service_map_compilation(self, service_map: Dict[str, Any], iterations: int = 100) -> Dict[str, Any]:
        """Benchmark full service map compilation."""
        print(f"Benchmarking service map compilation with {len(service_map)} patterns, {iterations} iterations...")
        
        compiler = YAMLCompiler()
        compiler.set_regions(['us-east', 'us-west', 'eu-central'])
        compiler.set_prefectures(['tokyo', 'osaka', 'kyoto'])
        
        def run_compilations():
            results = []
            for _ in range(iterations):
                compiled = compiler.compile_service_map(service_map)
                results.append(len(compiled['direct_mapping']))
            return results
        
        return self.profile_function(run_compilations)
    
    def benchmark_string_operations(self) -> Dict[str, Any]:
        """Benchmark string operations that are potential bottlenecks."""
        patterns = [
            'edge.*.gateway',
            'service-hub.*',
            'corebrain.*.processor',
            'app.*.env.*',
            'database.primary.cluster.*'
        ]
        
        results = {}
        
        # Benchmark split operations
        def test_split():
            results_list = []
            for _ in range(10000):
                for pattern in patterns:
                    parts = pattern.split('.')
                    results_list.append(len(parts))
            return results_list
        
        results['split_operation'] = self.profile_function(test_split)
        
        # Benchmark string joining
        def test_join():
            results_list = []
            for _ in range(10000):
                for pattern in patterns:
                    parts = pattern.split('.')
                    if len(parts) == 3:
                        joined = f"{parts[0]}.region.{parts[2]}"
                        results_list.append(len(joined))
            return results_list
        
        results['join_operation'] = self.profile_function(test_join)
        
        # Benchmark pattern matching
        def test_pattern_matching():
            results_list = []
            for _ in range(10000):
                for pattern in patterns:
                    parts = pattern.split('.')
                    if len(parts) == 3 and parts[0] == 'edge' and parts[1] == '*':
                        results_list.append(True)
                    else:
                        results_list.append(False)
            return results_list
        
        results['pattern_matching'] = self.profile_function(test_pattern_matching)
        
        return results


def generate_test_patterns(count: int) -> List[str]:
    """Generate test patterns for benchmarking."""
    patterns = []
    
    # Generate edge patterns
    for i in range(count // 4):
        role = f"role_{i % 10}"
        patterns.append(f"edge.*.{role}")
    
    # Generate service-hub patterns
    for i in range(count // 4):
        patterns.append("service-hub.*")
    
    # Generate corebrain patterns
    for i in range(count // 4):
        component = f"component_{i % 10}"
        patterns.append(f"corebrain.*.{component}")
    
    # Generate complex patterns
    for i in range(count - len(patterns)):
        app = f"app_{i % 5}"
        env = f"env_{i % 3}"
        patterns.append(f"{app}.*.{env}.*")
    
    return patterns


def generate_test_service_map(count: int) -> Dict[str, float]:
    """Generate test service map for benchmarking."""
    service_map = {}
    patterns = generate_test_patterns(count)
    
    for i, pattern in enumerate(patterns):
        service_map[pattern] = 0.01 + (i % 100) * 0.001
    
    return service_map


def run_baseline_benchmark():
    """Run baseline benchmark to identify bottlenecks."""
    profiler = PerformanceProfiler()
    
    print("=== YAML Config Compiler Performance Baseline ===\\n")
    
    # String operations benchmark
    print("1. String Operations Benchmark:")
    string_results = profiler.benchmark_string_operations()
    
    for operation, result in string_results.items():
        print(f"   {operation}: {result['execution_time']:.4f}s, "
              f"Memory: +{result['memory_increase_mb']:.2f}MB")
    
    print()
    
    # Pattern expansion benchmark - small scale
    print("2. Pattern Expansion Benchmark (100 patterns):")
    small_patterns = generate_test_patterns(100)
    small_result = profiler.benchmark_pattern_expansion(small_patterns, 100)
    
    print(f"   Time: {small_result['execution_time']:.4f}s")
    print(f"   Memory: +{small_result['memory_increase_mb']:.2f}MB")
    print(f"   Patterns/sec: {len(small_patterns) * 100 / small_result['execution_time']:.0f}")
    
    print()
    
    # Pattern expansion benchmark - medium scale
    print("3. Pattern Expansion Benchmark (1,000 patterns):")
    medium_patterns = generate_test_patterns(1000)
    medium_result = profiler.benchmark_pattern_expansion(medium_patterns, 10)
    
    print(f"   Time: {medium_result['execution_time']:.4f}s")
    print(f"   Memory: +{medium_result['memory_increase_mb']:.2f}MB")
    print(f"   Patterns/sec: {len(medium_patterns) * 10 / medium_result['execution_time']:.0f}")
    
    print()
    
    # Service map compilation benchmark
    print("4. Service Map Compilation Benchmark (1,000 patterns):")
    service_map = generate_test_service_map(1000)
    compilation_result = profiler.benchmark_service_map_compilation(service_map, 10)
    
    print(f"   Time: {compilation_result['execution_time']:.4f}s")
    print(f"   Memory: +{compilation_result['memory_increase_mb']:.2f}MB")
    print(f"   Compilations/sec: {10 / compilation_result['execution_time']:.2f}")
    
    print()
    
    # Large scale test
    print("5. Large Scale Test (10,000 patterns, 1 iteration):")
    large_patterns = generate_test_patterns(10000)
    large_result = profiler.benchmark_pattern_expansion(large_patterns, 1)
    
    print(f"   Time: {large_result['execution_time']:.4f}s")
    print(f"   Memory: +{large_result['memory_increase_mb']:.2f}MB")
    print(f"   Patterns/sec: {len(large_patterns) / large_result['execution_time']:.0f}")
    
    # Check if we meet the 1 second goal for 10k patterns
    if large_result['execution_time'] > 1.0:
        print(f"   ⚠️  PERFORMANCE ISSUE: 10k patterns took {large_result['execution_time']:.2f}s (goal: <1s)")
        print(f"   🎯 Need {large_result['execution_time']:.1f}x speedup to meet goal")
    else:
        print(f"   ✅ PERFORMANCE GOAL MET: 10k patterns in {large_result['execution_time']:.2f}s")
    
    print()
    
    # Detailed profiling for optimization targets
    print("6. Detailed Profiling (Medium Scale):")
    print("   Top function calls:")
    print(medium_result['profile_stats'].split('\\n')[:25])
    
    return {
        'string_operations': string_results,
        'small_scale': small_result,
        'medium_scale': medium_result,
        'large_scale': large_result,
        'compilation': compilation_result
    }


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import psutil
    except ImportError:
        print("Installing psutil for memory profiling...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    baseline_results = run_baseline_benchmark()
    
    # Save results
    benchmark_file = Path(__file__).parent / "baseline_results.txt"
    with open(benchmark_file, "w") as f:
        f.write("YAML Config Compiler Baseline Performance Results\\n")
        f.write("=" * 50 + "\\n\\n")
        
        for test_name, result in baseline_results.items():
            if isinstance(result, dict) and 'execution_time' in result:
                f.write(f"{test_name}:\\n")
                f.write(f"  Execution time: {result['execution_time']:.4f}s\\n")
                f.write(f"  Memory increase: {result['memory_increase_mb']:.2f}MB\\n\\n")
    
    print(f"\\nBaseline results saved to {benchmark_file}")
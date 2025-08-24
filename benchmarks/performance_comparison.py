"""Performance comparison between original and optimized implementations."""

import sys
import time
import gc
from pathlib import Path
from typing import Dict, Any, List
import psutil
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from yaml_config_compiler import YAMLCompiler as OriginalCompiler
from yaml_config_compiler.fast_compiler import FastYAMLCompiler as OptimizedCompiler


class PerformanceComparison:
    """Compare performance between original and optimized implementations."""
    
    def __init__(self):
        self.results = {}
        
    def benchmark_implementation(self, compiler_class, name: str, test_data: Dict[str, Any], iterations: int = 100) -> Dict[str, Any]:
        """Benchmark a compiler implementation."""
        print(f"Benchmarking {name}...")
        
        # Setup
        patterns = test_data['patterns']
        service_map = test_data['service_map']
        
        # Initialize compiler
        compiler = compiler_class()
        compiler.set_regions(['us-east-1', 'us-west-2', 'eu-central-1'])
        compiler.set_prefectures(['tokyo', 'osaka', 'kyoto', 'nagoya', 'fukuoka'])
        
        # Memory before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Warm up
        for _ in range(3):
            for pattern in patterns[:10]:
                compiler.expander.expand_pattern(pattern, 0.05)
        
        gc.collect()  # Force garbage collection
        
        # Benchmark pattern expansion
        start_time = time.perf_counter()
        
        expansion_results = []
        for _ in range(iterations):
            for pattern in patterns:
                result = compiler.expander.expand_pattern(pattern, 0.05)
                expansion_results.append(len(result))
        
        expansion_time = time.perf_counter() - start_time
        
        # Benchmark service map compilation
        start_time = time.perf_counter()
        
        compilation_results = []
        for _ in range(min(iterations, 50)):  # Limit compilations for large datasets
            result = compiler.compile_service_map(service_map)
            compilation_results.append(len(result['direct_mapping']))
        
        compilation_time = time.perf_counter() - start_time
        
        # Memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Get performance stats if available
        perf_stats = {}
        if hasattr(compiler, 'get_performance_stats'):
            try:
                perf_stats = compiler.get_performance_stats()
            except:
                pass
        
        return {
            'name': name,
            'expansion_time': expansion_time,
            'compilation_time': compilation_time,
            'total_time': expansion_time + compilation_time,
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_increase_mb': memory_after - memory_before,
            'patterns_processed': len(patterns) * iterations,
            'compilations_processed': min(iterations, 50),
            'patterns_per_second': (len(patterns) * iterations) / expansion_time,
            'compilations_per_second': min(iterations, 50) / compilation_time,
            'expansion_results_sample': expansion_results[:5],
            'compilation_results_sample': compilation_results[:3],
            'performance_stats': perf_stats
        }
    
    def generate_test_data(self, pattern_count: int) -> Dict[str, Any]:
        """Generate test data for benchmarking."""
        patterns = []
        service_map = {}
        
        # Generate varied patterns
        for i in range(pattern_count // 4):
            # Edge patterns
            role = f"role_{i % 20}"
            pattern = f"edge.*.{role}"
            patterns.append(pattern)
            service_map[pattern] = 0.01 + (i % 100) * 0.001
        
        for i in range(pattern_count // 4):
            # Service hub patterns
            pattern = "service-hub.*"
            if pattern not in patterns:
                patterns.append(pattern)
                service_map[pattern] = 0.02 + (i % 50) * 0.001
        
        for i in range(pattern_count // 4):
            # Corebrain patterns
            component = f"component_{i % 15}"
            pattern = f"corebrain.*.{component}"
            patterns.append(pattern)
            service_map[pattern] = 0.03 + (i % 75) * 0.001
        
        # Fill remaining with varied patterns
        remaining = pattern_count - len(patterns)
        for i in range(remaining):
            if i % 3 == 0:
                pattern = f"app_{i % 10}.*.env.*"
            elif i % 3 == 1:
                pattern = f"database.*.cluster_{i % 5}"
            else:
                pattern = f"service_{i % 20}.region.*"
            
            patterns.append(pattern)
            service_map[pattern] = 0.01 + (i % 200) * 0.0005
        
        return {
            'patterns': patterns[:pattern_count],
            'service_map': dict(list(service_map.items())[:min(pattern_count, len(service_map))])
        }
    
    def run_comparison(self, pattern_counts: List[int] = [100, 1000, 10000]) -> Dict[str, Any]:
        """Run comprehensive performance comparison."""
        print("=== Performance Comparison: Original vs Optimized ===\\n")
        
        results = {}
        
        for count in pattern_counts:
            print(f"\\n--- Testing with {count:,} patterns ---")
            
            test_data = self.generate_test_data(count)
            iterations = max(1, 1000 // count)  # Fewer iterations for larger datasets
            
            print(f"Generated {len(test_data['patterns'])} patterns, {len(test_data['service_map'])} service map entries")
            print(f"Running {iterations} iterations...")
            
            # Benchmark original implementation
            original_result = self.benchmark_implementation(
                OriginalCompiler, f"Original ({count:,})", test_data, iterations
            )
            
            # Benchmark optimized implementation
            optimized_result = self.benchmark_implementation(
                OptimizedCompiler, f"Optimized ({count:,})", test_data, iterations
            )
            
            # Calculate speedup
            expansion_speedup = original_result['expansion_time'] / optimized_result['expansion_time']
            compilation_speedup = original_result['compilation_time'] / optimized_result['compilation_time']
            total_speedup = original_result['total_time'] / optimized_result['total_time']
            
            # Memory efficiency
            memory_improvement = original_result['memory_increase_mb'] - optimized_result['memory_increase_mb']
            
            comparison = {
                'pattern_count': count,
                'original': original_result,
                'optimized': optimized_result,
                'speedup': {
                    'expansion': expansion_speedup,
                    'compilation': compilation_speedup,
                    'total': total_speedup
                },
                'memory_improvement_mb': memory_improvement,
                'patterns_per_second_improvement': (
                    optimized_result['patterns_per_second'] - original_result['patterns_per_second']
                )
            }
            
            results[count] = comparison
            
            # Print results
            print(f"\\nResults for {count:,} patterns:")
            print(f"  Original - Expansion: {original_result['expansion_time']:.4f}s, "
                  f"Compilation: {original_result['compilation_time']:.4f}s")
            print(f"  Optimized - Expansion: {optimized_result['expansion_time']:.4f}s, "
                  f"Compilation: {optimized_result['compilation_time']:.4f}s")
            print(f"  Speedup - Expansion: {expansion_speedup:.2f}x, "
                  f"Compilation: {compilation_speedup:.2f}x, Total: {total_speedup:.2f}x")
            print(f"  Memory improvement: {memory_improvement:+.2f}MB")
            print(f"  Patterns/sec - Original: {original_result['patterns_per_second']:,.0f}, "
                  f"Optimized: {optimized_result['patterns_per_second']:,.0f}")
            
            # Check if we meet the 10x goal
            if total_speedup >= 10.0:
                print(f"  + 10x SPEEDUP GOAL ACHIEVED! ({total_speedup:.2f}x)")
            elif total_speedup >= 5.0:
                print(f"  + Significant speedup achieved ({total_speedup:.2f}x)")
            elif total_speedup >= 2.0:
                print(f"  + Good speedup achieved ({total_speedup:.2f}x)")
            else:
                print(f"  - Limited speedup ({total_speedup:.2f}x)")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print summary of all results."""
        print("\\n" + "=" * 80)
        print("PERFORMANCE OPTIMIZATION SUMMARY")
        print("=" * 80)
        
        for count, comparison in results.items():
            speedup = comparison['speedup']['total']
            memory_improvement = comparison['memory_improvement_mb']
            
            print(f"\\n{count:,} patterns:")
            print(f"  Total speedup: {speedup:.2f}x")
            print(f"  Memory improvement: {memory_improvement:+.2f}MB")
            print(f"  Optimized patterns/sec: {comparison['optimized']['patterns_per_second']:,.0f}")
            
            # Performance stats from optimized implementation
            if comparison['optimized']['performance_stats']:
                stats = comparison['optimized']['performance_stats']
                if stats.get('use_optimized'):
                    print(f"  Cache efficiency:")
                    print(f"    Split cache: {stats.get('split_cache_size', 0)} entries")
                    print(f"    Match cache: {stats.get('match_cache_size', 0)} entries")
                    print(f"    Indexed patterns: {stats.get('exact_patterns', 0)} exact, "
                          f"{stats.get('indexed_two_part_patterns', 0)} two-part, "
                          f"{stats.get('indexed_three_part_patterns', 0)} three-part")
        
        # Overall assessment
        avg_speedup = sum(r['speedup']['total'] for r in results.values()) / len(results)
        
        print(f"\\nOVERALL ASSESSMENT:")
        print(f"  Average speedup: {avg_speedup:.2f}x")
        
        if avg_speedup >= 10.0:
            print(f"  STATUS: 10x PERFORMANCE GOAL ACHIEVED!")
        elif avg_speedup >= 5.0:
            print(f"  STATUS: Excellent performance improvement")
        elif avg_speedup >= 2.0:
            print(f"  STATUS: Good performance improvement")
        else:
            print(f"  STATUS: Limited improvement - further optimization needed")


def main():
    """Run the performance comparison."""
    print("YAML Config Compiler Performance Optimization\\n")
    print("Comparing original vs optimized implementations...")
    
    comparator = PerformanceComparison()
    
    # Run with different scales
    pattern_counts = [100, 1000, 5000, 10000]
    
    try:
        results = comparator.run_comparison(pattern_counts)
        comparator.print_summary(results)
        
        # Save detailed results
        results_file = Path(__file__).parent / "performance_comparison_results.txt"
        with open(results_file, "w") as f:
            f.write("YAML Config Compiler Performance Comparison Results\\n")
            f.write("=" * 60 + "\\n\\n")
            
            for count, comparison in results.items():
                f.write(f"{count:,} patterns:\\n")
                f.write(f"  Original total time: {comparison['original']['total_time']:.4f}s\\n")
                f.write(f"  Optimized total time: {comparison['optimized']['total_time']:.4f}s\\n")
                f.write(f"  Total speedup: {comparison['speedup']['total']:.2f}x\\n")
                f.write(f"  Memory improvement: {comparison['memory_improvement_mb']:+.2f}MB\\n\\n")
        
        print(f"\\nDetailed results saved to {results_file}")
        
    except Exception as e:
        print(f"\\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
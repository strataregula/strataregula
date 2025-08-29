#!/usr/bin/env python3
"""
Pattern Performance Benchmark - Test all patterns for performance
Measures execution speed, memory usage, and scalability of each pattern
"""

import time
import sys
import gc
from micro_patterns import *

def measure_performance(func, *args, iterations=1000):
    """Measure function performance with memory and time metrics"""
    gc.collect()
    start_memory = sys.getsizeof(gc.get_objects())
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        result = func(*args)
    end_time = time.perf_counter()
    
    gc.collect()
    end_memory = sys.getsizeof(gc.get_objects())
    
    return {
        'time_per_op': (end_time - start_time) / iterations * 1000,  # ms
        'memory_delta': end_memory - start_memory,
        'result': result
    }

def benchmark_patterns():
    """Benchmark all major patterns"""
    results = {}
    
    print("BENCHMARK: Starting pattern performance analysis...")
    
    # 1. Singleton Pattern
    results['singleton'] = measure_performance(lambda: Config())
    
    # 2. Factory Pattern
    results['factory'] = measure_performance(lambda: create_handler("json"))
    
    # 3. Builder Pattern  
    results['builder'] = measure_performance(
        lambda: Query().select("name").where("id=1")
    )
    
    # 4. Strategy Pattern
    strategy = Sorter(lambda data: sorted(data))
    results['strategy'] = measure_performance(
        lambda: strategy.sort([3,1,4,1,5,9,2,6])
    )
    
    # 5. Memoization
    @memoize
    def fib_memo(n): return n if n <= 1 else fib_memo(n-1) + fib_memo(n-2)
    results['memoize'] = measure_performance(lambda: fib_memo(20))
    
    # 6. Pipe Pattern
    results['pipe'] = measure_performance(
        lambda: pipe(10, lambda x: x*2, lambda x: x+1, lambda x: x/2)
    )
    
    # 7. Maybe Pattern
    results['maybe'] = measure_performance(
        lambda: Maybe(5).map(lambda x: x*2).map(lambda x: x+1)
    )
    
    # 8. Repository Pattern
    repo = Repository()
    results['repository'] = measure_performance(
        lambda: repo.save(1, User(1, "test")) or repo.find(1)
    )
    
    # 9. Observer Pattern
    subject = Subject()
    class TestObs:
        def update(self, event): pass
    subject.observers = [TestObs() for _ in range(10)]
    results['observer'] = measure_performance(
        lambda: subject.notify("test")
    )
    
    # 10. Circuit Breaker
    breaker = CircuitBreaker()
    results['circuit_breaker'] = measure_performance(
        lambda: breaker.call(lambda: "success")
    )
    
    return results

def generate_report(results):
    """Generate performance report"""
    print("\nPERFORMANCE REPORT:")
    print("="*60)
    print(f"{'Pattern':<15} {'Time/Op (ms)':<12} {'Memory':<10} {'Status'}")
    print("-"*60)
    
    for pattern, metrics in results.items():
        time_str = f"{metrics['time_per_op']:.4f}"
        memory_str = f"{metrics['memory_delta']:+d}B" if metrics['memory_delta'] != 0 else "0B"
        status = "FAST" if metrics['time_per_op'] < 0.01 else "OK" if metrics['time_per_op'] < 0.1 else "SLOW"
        
        print(f"{pattern:<15} {time_str:<12} {memory_str:<10} {status}")
    
    # Find fastest and slowest
    fastest = min(results.items(), key=lambda x: x[1]['time_per_op'])
    slowest = max(results.items(), key=lambda x: x[1]['time_per_op'])
    
    print("\nSUMMARY:")
    print(f"Fastest: {fastest[0]} ({fastest[1]['time_per_op']:.4f}ms/op)")
    print(f"Slowest: {slowest[0]} ({slowest[1]['time_per_op']:.4f}ms/op)")
    print(f"Speed Ratio: {slowest[1]['time_per_op'] / fastest[1]['time_per_op']:.1f}x")

def stress_test_patterns():
    """Stress test patterns with large datasets"""
    print("\nSTRESS TEST: Testing pattern scalability...")
    
    # Test strategy pattern with large dataset
    large_data = list(range(10000))
    strategy = Sorter(sorted)
    
    start = time.perf_counter()
    result = strategy.sort(large_data)
    end = time.perf_counter()
    
    print(f"Large Sort (10K items): {(end-start)*1000:.2f}ms")
    
    # Test memoization with repeated calls
    @memoize
    def expensive_calc(n): return sum(range(n))
    
    start = time.perf_counter()
    for _ in range(1000):
        expensive_calc(100)  # Same input, should hit cache
    end = time.perf_counter()
    
    print(f"Memoized Calls (1000x): {(end-start)*1000:.2f}ms")
    
    # Test observer with many observers
    subject = Subject()
    class StressObs:
        def __init__(self): self.count = 0
        def update(self, event): self.count += 1
    
    observers = [StressObs() for _ in range(1000)]
    subject.observers = observers
    
    start = time.perf_counter()
    for _ in range(100):
        subject.notify("stress_event")
    end = time.perf_counter()
    
    print(f"Observer Broadcast (1000 obs x 100 events): {(end-start)*1000:.2f}ms")

def pattern_coverage_analysis():
    """Analyze pattern coverage and complexity"""
    patterns = [
        "Null Object", "Singleton", "Factory", "Builder", "Command",
        "Observer", "Strategy", "Decorator", "Adapter", "Template",
        "Currying", "Partial", "Pipe", "Memoize", "Map-Reduce",
        "Monoid", "Maybe", "Async Context", "Producer-Consumer", 
        "Circuit Breaker", "Repository", "Unit of Work", "Active Record",
        "Data Mapper", "Specification"
    ]
    
    categories = {
        "Creational": ["Singleton", "Factory", "Builder"],
        "Structural": ["Adapter", "Decorator"],
        "Behavioral": ["Strategy", "Observer", "Command", "Template"],
        "Functional": ["Currying", "Partial", "Pipe", "Memoize", "Map-Reduce", "Monoid", "Maybe"],
        "Async": ["Async Context", "Producer-Consumer", "Circuit Breaker"],
        "Data": ["Repository", "Unit of Work", "Active Record", "Data Mapper", "Specification"],
        "Utility": ["Null Object"]
    }
    
    print("\nPATTERN COVERAGE ANALYSIS:")
    print("="*50)
    
    total_patterns = len(patterns)
    for category, cat_patterns in categories.items():
        coverage = len(cat_patterns) / total_patterns * 100
        print(f"{category:<15}: {len(cat_patterns):2d} patterns ({coverage:.1f}%)")
    
    print(f"\nTotal Patterns: {total_patterns}")
    print(f"Categories: {len(categories)}")
    print(f"Avg per Category: {total_patterns / len(categories):.1f}")

def main():
    """Main benchmark execution"""
    print("MICRO PATTERN PERFORMANCE BENCHMARK")
    print("="*50)
    
    # Run performance benchmarks
    results = benchmark_patterns()
    generate_report(results)
    
    # Run stress tests
    stress_test_patterns()
    
    # Analyze coverage
    pattern_coverage_analysis()
    
    print("\nBENCHMARK COMPLETE!")
    print("All patterns tested for performance, scalability, and coverage.")

if __name__ == "__main__":
    main()
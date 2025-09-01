# Python Performance Best Practices

## Overview
Python-specific optimization techniques for pattern processing, compilation, and stream operations in Strataregula.

## Core Optimization Principles

### 1. Data Structure Selection

```python
# ❌ List for membership testing
items = ['apple', 'banana', 'cherry']
if 'apple' in items:  # O(n) linear search
    process_item()

# ✅ Set for membership testing  
items = {'apple', 'banana', 'cherry'}
if 'apple' in items:  # O(1) hash lookup
    process_item()

# ✅ Dict for key-value mapping
config = {'timeout': 30, 'retries': 3}
timeout = config['timeout']  # O(1) access
```

### 2. Loop Optimization

```python
# ❌ Inefficient loops
results = []
for item in items:
    if condition(item):
        results.append(transform(item))

# ✅ List comprehensions (faster and more readable)
results = [transform(item) for item in items if condition(item)]

# ✅ Generator expressions for memory efficiency
results = (transform(item) for item in items if condition(item))

# ✅ Built-in functions when applicable
results = list(map(transform, filter(condition, items)))
```

### 3. String Operations

```python
# ❌ String concatenation in loops
result = ""
for item in items:
    result += str(item) + "\n"  # Creates new string each time

# ✅ Join operation
result = "\n".join(str(item) for item in items)

# ✅ f-strings for formatting (Python 3.6+)
message = f"Processing {item.name} with {item.count} items"
```

## Memory Management

### 1. Generator Usage

```python
# ❌ Memory-intensive: Load all data into memory
def process_large_file(filename):
    lines = open(filename).readlines()  # Loads entire file
    return [process_line(line) for line in lines]

# ✅ Memory-efficient: Stream processing
def process_large_file(filename):
    with open(filename) as f:
        return (process_line(line) for line in f)

# ✅ Chunk processing for balanced approach
def process_in_chunks(iterable, chunk_size=1000):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
```

### 2. Object Creation Optimization

```python
# ❌ Expensive object creation in loops
results = []
for data in dataset:
    obj = ComplexObject(data)  # Heavy constructor
    results.append(obj.process())

# ✅ Object pooling
class ObjectPool:
    def __init__(self, factory, size=10):
        self._factory = factory
        self._pool = [factory() for _ in range(size)]
        self._available = list(self._pool)
    
    def get(self):
        return self._available.pop() if self._available else self._factory()
    
    def return_object(self, obj):
        obj.reset()  # Clean state
        self._available.append(obj)

# Usage
pool = ObjectPool(lambda: ComplexObject(), size=50)
results = []
for data in dataset:
    obj = pool.get()
    try:
        obj.configure(data)
        results.append(obj.process())
    finally:
        pool.return_object(obj)
```

### 3. Memory-Efficient Data Processing

```python
# Pattern from strataregula's stream processing
def efficient_pattern_expansion(patterns):
    """Memory-efficient pattern expansion based on existing architecture"""
    
    # Use generators to avoid loading all patterns into memory
    def expand_single_pattern(pattern):
        # Actual expansion logic here
        yield from compile_pattern(pattern)
    
    # Stream processing without intermediate collections
    for pattern in patterns:
        yield from expand_single_pattern(pattern)

# Integration with existing ConfigCompiler
class OptimizedPatternExpander:
    def expand_pattern_stream(self, patterns):
        """Optimized version of existing expand_pattern_stream"""
        for pattern_key, pattern_value in patterns.items():
            # Use existing compilation logic but stream results
            compiled = self._compile_pattern_cached(pattern_key, pattern_value)
            yield from compiled
    
    @lru_cache(maxsize=1024)
    def _compile_pattern_cached(self, key, value):
        """Cache compiled patterns to avoid recompilation"""
        return self._compile_pattern(key, value)
```

## Algorithm Optimization

### 1. Search and Lookup Optimization

```python
# Example from pattern matching optimization
class OptimizedPatternMatcher:
    def __init__(self, patterns):
        # Pre-process patterns for faster matching
        self.exact_patterns = {}
        self.wildcard_patterns = []
        self.compiled_regex = []
        
        for pattern in patterns:
            if '*' not in pattern and '?' not in pattern:
                # Exact match - use dict lookup O(1)
                self.exact_patterns[pattern] = True
            elif pattern.count('*') <= 2:
                # Simple wildcard - use fnmatch
                self.wildcard_patterns.append(pattern)
            else:
                # Complex pattern - use compiled regex
                self.compiled_regex.append(re.compile(pattern))
    
    def match(self, text):
        # Try exact match first (fastest)
        if text in self.exact_patterns:
            return True
        
        # Try simple wildcards
        for pattern in self.wildcard_patterns:
            if fnmatch.fnmatch(text, pattern):
                return True
        
        # Try regex patterns (slowest)
        for regex in self.compiled_regex:
            if regex.match(text):
                return True
        
        return False
```

### 2. Caching Strategies

```python
from functools import lru_cache, wraps
import time

# LRU Cache for function results
@lru_cache(maxsize=128)
def expensive_computation(param):
    """Cached computation - from existing patterns"""
    time.sleep(0.1)  # Simulate expensive operation
    return param * 2

# TTL Cache for time-sensitive data
class TTLCache:
    def __init__(self, ttl_seconds=300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key, factory_func):
        now = time.time()
        if key in self.cache:
            value, timestamp = self.cache[key]
            if now - timestamp < self.ttl:
                return value
        
        # Cache miss or expired
        value = factory_func()
        self.cache[key] = (value, now)
        return value
    
    def clear_expired(self):
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]

# Usage in pattern compilation
pattern_cache = TTLCache(ttl_seconds=600)  # 10 minute cache

def get_compiled_pattern(pattern_text):
    return pattern_cache.get(
        pattern_text,
        lambda: compile_pattern_expensive(pattern_text)
    )
```

## Performance Measurement Framework

### 1. Accurate Timing

```python
import time
import statistics
from typing import Callable, Dict, Any, List

def benchmark_function(
    func: Callable,
    *args,
    iterations: int = 1000,
    warmup: int = 100,
    **kwargs
) -> Dict[str, float]:
    """
    Accurate function benchmarking with statistical analysis.
    Based on optimized_benchmark.py patterns.
    """
    # Warmup phase (important for JIT optimizations)
    for _ in range(warmup):
        func(*args, **kwargs)
    
    # Measurement phase
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        times.append((time.perf_counter() - start) * 1_000_000)  # μs
    
    # Statistical analysis
    times_sorted = sorted(times)
    n = len(times_sorted)
    
    return {
        'mean_us': statistics.mean(times),
        'median_us': times_sorted[n // 2],
        'p95_us': times_sorted[int(0.95 * n)],
        'p99_us': times_sorted[int(0.99 * n)],
        'min_us': min(times),
        'max_us': max(times),
        'std_us': statistics.stdev(times) if n > 1 else 0.0,
        'iterations': iterations
    }
```

### 2. Memory Profiling

```python
import gc
import sys
from typing import Any

def measure_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Measure memory impact of function execution"""
    
    # Force garbage collection and get baseline
    gc.collect()
    memory_before = sys.getsizeof(gc.get_objects())
    
    # Execute function
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    
    # Measure memory after execution
    gc.collect()
    memory_after = sys.getsizeof(gc.get_objects())
    
    return {
        'result': result,
        'execution_time_ms': (end_time - start_time) * 1000,
        'memory_delta_bytes': memory_after - memory_before,
        'memory_delta_mb': (memory_after - memory_before) / (1024 * 1024)
    }
```

### 3. Comparative Benchmarking

```python
def compare_implementations(
    implementations: Dict[str, Callable],
    test_data: Any,
    iterations: int = 1000
) -> Dict[str, Dict[str, float]]:
    """
    Compare multiple implementations of the same functionality.
    Returns detailed performance comparison.
    """
    results = {}
    
    for name, func in implementations.items():
        print(f"Benchmarking: {name}")
        results[name] = benchmark_function(func, test_data, iterations=iterations)
    
    # Calculate relative performance
    fastest = min(results.values(), key=lambda x: x['mean_us'])
    fastest_time = fastest['mean_us']
    
    for name, metrics in results.items():
        metrics['relative_speed'] = metrics['mean_us'] / fastest_time
        metrics['speedup'] = fastest_time / metrics['mean_us']
    
    return results

def print_comparison_report(results: Dict[str, Dict[str, float]]):
    """Generate readable comparison report"""
    print("\nPerformance Comparison Report")
    print("=" * 80)
    print(f"{'Implementation':<20} {'Mean (μs)':<12} {'P95 (μs)':<12} {'Relative':<10} {'Status'}")
    print("-" * 80)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['mean_us'])
    
    for name, metrics in sorted_results:
        status = '🚀 FAST' if metrics['relative_speed'] < 1.5 else \
                '✅ OK' if metrics['relative_speed'] < 3.0 else \
                '⚠️ SLOW'
        
        print(f"{name:<20} {metrics['mean_us']:<12.2f} {metrics['p95_us']:<12.2f} "
              f"{metrics['relative_speed']:<10.1f}x {status}")
```

## Strataregula-Specific Optimizations

### 1. Pattern Compilation Performance

```python
# Based on existing ConfigCompiler architecture
class HighPerformanceCompiler:
    def __init__(self):
        self._pattern_cache = {}
        self._compiled_regex_cache = {}
    
    def compile_patterns_optimized(self, patterns: Dict[str, Any]) -> Iterator[Any]:
        """
        Optimized pattern compilation with caching and streaming.
        Extends existing compiler.py functionality.
        """
        # Group patterns by complexity for optimal processing
        simple_patterns = {}
        complex_patterns = {}
        
        for key, value in patterns.items():
            if self._is_simple_pattern(key):
                simple_patterns[key] = value
            else:
                complex_patterns[key] = value
        
        # Process simple patterns first (batch optimization)
        yield from self._compile_simple_batch(simple_patterns)
        
        # Process complex patterns with caching
        for key, value in complex_patterns.items():
            cache_key = hash((key, str(value)))
            if cache_key not in self._pattern_cache:
                self._pattern_cache[cache_key] = self._compile_complex_pattern(key, value)
            yield self._pattern_cache[cache_key]
    
    def _is_simple_pattern(self, pattern: str) -> bool:
        """Classify patterns by complexity for optimal processing"""
        return '*' not in pattern and '?' not in pattern and '{' not in pattern
    
    def _compile_simple_batch(self, patterns: Dict[str, Any]) -> Iterator[Any]:
        """Batch process simple patterns for efficiency"""
        # Use vectorized operations where possible
        return (self._simple_compile(k, v) for k, v in patterns.items())
    
    def _compile_complex_pattern(self, key: str, value: Any) -> Any:
        """Compile complex patterns with regex caching"""
        # Reuse compiled regex objects
        if key not in self._compiled_regex_cache:
            self._compiled_regex_cache[key] = re.compile(self._pattern_to_regex(key))
        
        regex = self._compiled_regex_cache[key]
        return self._apply_compiled_regex(regex, value)
```

### 2. Stream Processing Optimization

```python
# Optimized stream processing based on existing stream/ module
class OptimizedStreamProcessor:
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self._buffer = []
    
    def process_stream(self, data_stream: Iterator[Any]) -> Iterator[Any]:
        """
        Process streaming data with optimal batching.
        Extends existing stream/processor.py functionality.
        """
        for item in data_stream:
            self._buffer.append(item)
            
            if len(self._buffer) >= self.chunk_size:
                # Process full chunk
                yield from self._process_chunk(self._buffer)
                self._buffer.clear()
        
        # Process remaining items
        if self._buffer:
            yield from self._process_chunk(self._buffer)
    
    def _process_chunk(self, chunk: List[Any]) -> Iterator[Any]:
        """Optimized chunk processing with minimal overhead"""
        # Use bulk operations where possible
        return self._bulk_transform(chunk)
    
    def _bulk_transform(self, items: List[Any]) -> Iterator[Any]:
        """Vectorized transformations for better performance"""
        # Example: batch regex operations
        if hasattr(self, '_compiled_patterns'):
            return self._apply_patterns_bulk(items)
        return items
```

### 3. Memory Pool Management

```python
from typing import TypeVar, Generic, List, Optional
import weakref

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """
    Object pool for expensive-to-create objects.
    Reduces garbage collection pressure.
    """
    def __init__(self, factory: Callable[[], T], max_size: int = 50):
        self._factory = factory
        self._pool: List[T] = []
        self._max_size = max_size
        self._created_count = 0
    
    def acquire(self) -> T:
        """Get an object from the pool or create new one"""
        if self._pool:
            return self._pool.pop()
        
        self._created_count += 1
        return self._factory()
    
    def release(self, obj: T) -> None:
        """Return object to pool for reuse"""
        if len(self._pool) < self._max_size:
            # Reset object state if needed
            if hasattr(obj, 'reset'):
                obj.reset()
            self._pool.append(obj)
    
    def stats(self) -> Dict[str, int]:
        return {
            'pool_size': len(self._pool),
            'created_total': self._created_count,
            'max_size': self._max_size
        }

# Usage for expensive pattern objects
pattern_pool = ObjectPool(lambda: ComplexPatternMatcher(), max_size=20)

def process_patterns_with_pool(patterns):
    matcher = pattern_pool.acquire()
    try:
        return matcher.process_all(patterns)
    finally:
        pattern_pool.release(matcher)
```

## Advanced Optimization Techniques

### 1. Compilation and Caching

```python
import ast
import types
from functools import lru_cache

class CompiledPatternCache:
    """
    Advanced pattern compilation with bytecode caching.
    Extends existing pattern compilation architecture.
    """
    def __init__(self, max_cache_size: int = 1000):
        self._source_cache = {}
        self._bytecode_cache = {}
        self._max_size = max_cache_size
    
    def get_compiled_function(self, pattern: str) -> Callable:
        """Get compiled function for pattern matching"""
        cache_key = hash(pattern)
        
        if cache_key not in self._bytecode_cache:
            # Generate optimized code
            source_code = self._generate_matcher_code(pattern)
            
            # Compile to bytecode
            compiled_code = compile(source_code, '<dynamic>', 'exec')
            
            # Execute to create function
            namespace = {}
            exec(compiled_code, namespace)
            
            self._bytecode_cache[cache_key] = namespace['pattern_matcher']
            
            # Manage cache size
            if len(self._bytecode_cache) > self._max_size:
                self._evict_oldest()
        
        return self._bytecode_cache[cache_key]
    
    def _generate_matcher_code(self, pattern: str) -> str:
        """Generate optimized Python code for pattern matching"""
        # Analyze pattern and generate specialized code
        if '*' not in pattern:
            return f"def pattern_matcher(text): return text == '{pattern}'"
        elif pattern.endswith('*'):
            prefix = pattern[:-1]
            return f"def pattern_matcher(text): return text.startswith('{prefix}')"
        else:
            # Fall back to regex for complex patterns
            escaped = re.escape(pattern).replace(r'\*', '.*')
            return f"""
import re
_compiled_regex = re.compile(r'^{escaped}$')
def pattern_matcher(text): 
    return _compiled_regex.match(text) is not None
"""
```

### 2. Asynchronous Processing

```python
import asyncio
from typing import AsyncIterator

class AsyncPatternProcessor:
    """
    Asynchronous pattern processing for I/O bound operations.
    Integrates with existing async patterns in protocols/websocket.py
    """
    def __init__(self, max_concurrent: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_files_async(self, file_paths: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """Process multiple files concurrently"""
        tasks = [self._process_single_file(path) for path in file_paths]
        
        # Process in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in results:
                if not isinstance(result, Exception):
                    yield result
    
    async def _process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Process single file with concurrency control"""
        async with self.semaphore:
            # Use async file I/O for better concurrency
            import aiofiles
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return self._analyze_content(content, file_path)
```

## Performance Testing Integration

### 1. Automated Performance Tests

```python
import pytest
import time
from pathlib import Path

class TestPerformance:
    """Performance test suite integrated with existing test architecture"""
    
    @pytest.mark.performance
    def test_pattern_compilation_speed(self):
        """Test pattern compilation performance requirements"""
        from strataregula.core.pattern_expander import PatternExpander
        
        # Generate test patterns
        patterns = {f"service.{i}.config": f"value_{i}" for i in range(1000)}
        
        expander = PatternExpander()
        
        # Benchmark compilation
        start_time = time.perf_counter()
        results = list(expander.expand_pattern_stream(patterns))
        end_time = time.perf_counter()
        
        # Performance assertions
        duration = end_time - start_time
        throughput = len(results) / duration
        
        assert throughput > 1000, f"Throughput {throughput:.0f} < 1000 patterns/second"
        assert duration < 5.0, f"Duration {duration:.2f}s > 5.0s limit"
    
    @pytest.mark.performance
    def test_memory_efficiency(self):
        """Test memory usage stays within bounds"""
        import gc
        
        gc.collect()
        memory_before = self._get_memory_usage()
        
        # Execute memory-intensive operation
        large_dataset = self._create_large_dataset(10000)
        processed = list(self._process_dataset(large_dataset))
        
        gc.collect()
        memory_after = self._get_memory_usage()
        
        memory_used_mb = (memory_after - memory_before) / (1024 * 1024)
        
        assert memory_used_mb < 100, f"Memory usage {memory_used_mb:.1f}MB > 100MB limit"
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except ImportError:
            # Fallback method
            return sum(sys.getsizeof(obj) for obj in gc.get_objects())
```

### 2. Performance Regression Detection

```python
import json
from pathlib import Path
from typing import Dict, Any

class PerformanceRegression:
    """
    Performance regression detection system.
    Integrates with existing bench_guard.py functionality.
    """
    def __init__(self, baseline_file: str = "performance_baseline.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline_data = self._load_baseline()
    
    def _load_baseline(self) -> Dict[str, Any]:
        """Load performance baseline data"""
        if self.baseline_file.exists():
            return json.loads(self.baseline_file.read_text())
        return {}
    
    def check_regression(self, current_metrics: Dict[str, float], tolerance: float = 0.1) -> bool:
        """
        Check if current performance represents a regression.
        
        Args:
            current_metrics: Current performance measurements
            tolerance: Acceptable performance degradation (10% default)
        
        Returns:
            True if performance is acceptable, False if regression detected
        """
        if not self.baseline_data:
            # No baseline - establish current as baseline
            self._save_baseline(current_metrics)
            return True
        
        regressions = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name in self.baseline_data:
                baseline_value = self.baseline_data[metric_name]
                
                # Check for regression (higher is worse for timing metrics)
                if metric_name.endswith('_us') or metric_name.endswith('_ms'):
                    degradation = (current_value - baseline_value) / baseline_value
                    if degradation > tolerance:
                        regressions.append({
                            'metric': metric_name,
                            'baseline': baseline_value,
                            'current': current_value,
                            'degradation_pct': degradation * 100
                        })
        
        if regressions:
            print("🚨 Performance Regressions Detected:")
            for reg in regressions:
                print(f"  {reg['metric']}: {reg['baseline']:.2f} → {reg['current']:.2f} "
                      f"({reg['degradation_pct']:.1f}% slower)")
            return False
        
        return True
    
    def _save_baseline(self, metrics: Dict[str, float]) -> None:
        """Save current metrics as new baseline"""
        self.baseline_data = metrics
        self.baseline_file.write_text(json.dumps(metrics, indent=2))
```

## Python-Specific Anti-Patterns

### 1. Common Performance Mistakes

```python
# ❌ String concatenation in loops
result = ""
for item in items:
    result += process(item)  # O(n²) complexity

# ❌ Unnecessary list creation
sum([x * 2 for x in range(1000000)])  # Creates full list in memory

# ❌ Global variable access in tight loops
global_config = {'multiplier': 2}
def slow_process(items):
    return [item * global_config['multiplier'] for item in items]

# ❌ Exception handling for control flow
def slow_get(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        return None
```

### 2. Optimized Alternatives

```python
# ✅ String join operation
result = "".join(process(item) for item in items)

# ✅ Generator expression
sum(x * 2 for x in range(1000000))  # Memory efficient

# ✅ Local variable caching
def fast_process(items):
    multiplier = global_config['multiplier']  # Cache locally
    return [item * multiplier for item in items]

# ✅ Explicit checking
def fast_get(dictionary, key):
    return dictionary.get(key)  # Built-in default handling
```

## Profiling and Debugging

### 1. Function-Level Profiling

```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator for function-level profiling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
        
        # Generate report
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

# Usage
@profile_function
def expensive_pattern_processing(patterns):
    # Function to profile
    return process_patterns(patterns)
```

### 2. Memory Profiling

```python
from memory_profiler import profile
import tracemalloc

@profile  # Requires memory_profiler package
def memory_intensive_function():
    # Function to profile for memory usage
    pass

def trace_memory_allocations():
    """Track memory allocations for debugging"""
    tracemalloc.start()
    
    # Code to analyze
    result = expensive_operation()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()
    return result
```

## Performance Checklist

### Pre-Development
- [ ] Analyze algorithmic complexity requirements
- [ ] Choose appropriate data structures
- [ ] Plan for memory-efficient processing
- [ ] Identify caching opportunities

### During Development
- [ ] Use list comprehensions over manual loops
- [ ] Cache expensive computations with `@lru_cache`
- [ ] Prefer generators for large datasets
- [ ] Use built-in functions when available

### Testing
- [ ] Write performance tests for critical functions
- [ ] Benchmark with realistic data sizes
- [ ] Test memory usage with large datasets
- [ ] Validate performance requirements

### Optimization
- [ ] Profile to identify actual bottlenecks
- [ ] Optimize hot paths first (80/20 rule)
- [ ] Use appropriate caching strategies
- [ ] Consider async processing for I/O bound operations

## Integration with Strataregula Architecture

The Python optimizations integrate seamlessly with existing components:

1. **ConfigCompiler**: Enhanced pattern compilation with caching
2. **Stream Processing**: Optimized chunking and batch operations  
3. **Plugin System**: Performance-aware plugin loading and execution
4. **Index Operations**: Efficient content search and retrieval
5. **JSON Processing**: Optimized parsing and transformation

## Performance Goals

- **Pattern Compilation**: >1000 patterns/second
- **Stream Processing**: <10MB memory per 1000 items
- **Index Operations**: <100ms for typical searches
- **Plugin Loading**: <50ms initialization time
- **JSON Processing**: >500 objects/second transformation rate
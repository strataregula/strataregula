# Performance Optimization Principles

## Core Philosophy

**Measure First, Optimize Second**
- Never assume where bottlenecks exist
- Profile before optimizing
- Validate improvements with metrics
- Document performance impact

## Optimization Hierarchy

### 1. Algorithm Complexity (O-notation)
Most impactful optimization level - focus here first.

```python
# ❌ O(n²) - Quadratic complexity
def slow_search(items, target):
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == target:
                return i
    return -1

# ✅ O(log n) - Logarithmic complexity  
def fast_search(sorted_items, target):
    return bisect.bisect_left(sorted_items, target)
```

### 2. Data Structures
Choose appropriate data structures for access patterns.

```python
# ❌ List for frequent lookups
users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
user = next(u for u in users if u["id"] == 1)  # O(n)

# ✅ Dictionary for key-based access
users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
user = users[1]  # O(1)
```

### 3. Memory Access Patterns
Optimize for CPU cache locality and memory efficiency.

```python
# ❌ Random memory access
def process_sparse(data):
    indices = [random.randint(0, len(data)-1) for _ in range(1000)]
    return [data[i] for i in indices]

# ✅ Sequential memory access
def process_sequential(data):
    return [item for item in data[:1000]]
```

### 4. I/O Optimization
Minimize system calls and optimize file operations.

```powershell
# ❌ Multiple file reads
foreach ($file in $files) {
    $content = Get-Content $file  # Separate I/O call per file
    Process-Content $content
}

# ✅ Batch file operations
$allContent = $files | ForEach-Object { Get-Content $_ }
Process-AllContent $allContent
```

## Performance Measurement Standards

### Statistical Significance
- **Minimum iterations**: 1000 for micro-benchmarks
- **Warmup period**: Account for JIT compilation and caching
- **Multiple runs**: Detect and account for variance
- **Percentile reporting**: p50, p95, p99 for latency distribution

### Measurement Accuracy
```python
import time

# ❌ Single measurement
start = time.time()
result = slow_function()
print(f"Time: {time.time() - start}")

# ✅ Statistical measurement
def benchmark_function(func, iterations=1000):
    # Warmup
    for _ in range(100):
        func()
    
    # Measure
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)
    
    return {
        'mean': statistics.mean(times),
        'p95': sorted(times)[int(0.95 * len(times))],
        'min': min(times),
        'max': max(times)
    }
```

## Optimization Patterns

### 1. Lazy Evaluation
Defer expensive computations until needed.

```python
class LazyConfig:
    def __init__(self):
        self._compiled = None
    
    @property
    def compiled(self):
        if self._compiled is None:
            self._compiled = expensive_compilation()
        return self._compiled
```

### 2. Memoization
Cache expensive function results.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param):
    # Heavy computation
    return result
```

### 3. Batch Processing
Process multiple items together to reduce overhead.

```python
# ❌ Individual processing
for item in items:
    process_single(item)

# ✅ Batch processing
process_batch(items)
```

### 4. Resource Pooling
Reuse expensive objects instead of recreating.

```python
class ConnectionPool:
    def __init__(self, size=10):
        self._pool = [create_connection() for _ in range(size)]
        self._available = list(self._pool)
    
    def get_connection(self):
        return self._available.pop() if self._available else None
```

## Performance Anti-Patterns

### 1. Premature Optimization
```python
# ❌ Optimizing before measuring
def over_optimized_function():
    # Complex optimization for unproven bottleneck
    pass

# ✅ Profile-guided optimization
def profile_then_optimize():
    # Measure first, then optimize proven bottlenecks
    pass
```

### 2. Micro-Optimization Obsession
Focus on algorithmic improvements over micro-optimizations.

### 3. Memory Leaks
```python
# ❌ Accumulating references
class LeakyCache:
    def __init__(self):
        self.cache = {}  # Never cleared
    
    def get(self, key):
        if key not in self.cache:
            self.cache[key] = expensive_operation(key)
        return self.cache[key]

# ✅ Bounded cache
from functools import lru_cache

@lru_cache(maxsize=128)  # Automatic eviction
def cached_operation(key):
    return expensive_operation(key)
```

## Performance Testing Strategy

### 1. Unit Performance Tests
Test individual function performance in isolation.

### 2. Integration Performance Tests
Test performance of combined components.

### 3. Load Testing
Test behavior under realistic workloads.

### 4. Stress Testing
Test behavior beyond normal capacity.

### 5. Regression Testing
Detect performance degradation over time.

## Success Metrics

### Primary Metrics
- **Throughput**: Operations per second
- **Latency**: Response time distribution (p50, p95, p99)
- **Resource Usage**: CPU, memory, I/O utilization
- **Scalability**: Performance under increasing load

### Secondary Metrics
- **Error Rate**: Failures under load
- **Recovery Time**: Time to recover from failures
- **Resource Efficiency**: Work done per resource unit
- **User Experience**: Perceived performance

## Tools and Frameworks

### Python
- `time.perf_counter()` for high-precision timing
- `cProfile` for function-level profiling
- `memory_profiler` for memory usage analysis
- `pytest-benchmark` for automated benchmarking

### PowerShell
- `Measure-Command` for execution timing
- `Get-Process` for memory usage tracking
- Custom timing functions for micro-benchmarks

### Cross-Language
- `bench_guard.py` for regression detection
- `perf_suite.py` for comprehensive testing
- Historical data tracking for trend analysis

## Best Practices Summary

1. **Profile before optimizing** - Measure to find real bottlenecks
2. **Optimize algorithms first** - Focus on O-notation improvements
3. **Cache expensive operations** - Memoization and result caching
4. **Batch operations** - Reduce overhead through batching
5. **Use appropriate data structures** - Match structure to access pattern
6. **Minimize I/O operations** - Batch file operations when possible
7. **Test performance continuously** - Automated regression detection
8. **Document optimization decisions** - Track rationale and impact
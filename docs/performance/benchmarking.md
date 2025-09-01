# Benchmarking Framework Guide

## Overview
Comprehensive benchmarking framework for measuring, comparing, and tracking performance across Python and PowerShell implementations in Strataregula.

## Framework Architecture

```
benchmarks/
├── perf_suite.py           # Main Python benchmarking framework
├── results/                # Benchmark results storage
│   ├── baseline.json       # Performance baselines
│   ├── comprehensive_*     # Full benchmark runs  
│   └── regression_*        # Regression test results
└── temp/                   # Temporary files for cross-language testing

scripts/
├── perf_analyzer.ps1       # PowerShell performance analyzer
└── bench_guard.py          # Existing regression guard

tools/
├── perf_reporter.py        # Results analysis and reporting
└── performance.db          # SQLite database for historical tracking
```

## Quick Start Guide

### 1. Run Basic Performance Test

```bash
# Python comprehensive benchmark
python benchmarks/perf_suite.py

# PowerShell performance analysis  
pwsh scripts/perf_analyzer.ps1

# Specific module benchmark
python benchmarks/perf_suite.py --module core.compiler --size 5000
```

### 2. Performance Regression Testing

```bash
# Python regression test
python benchmarks/perf_suite.py --regression-test

# PowerShell regression test
pwsh scripts/perf_analyzer.ps1 -RegressionTest

# Combined regression analysis
python tools/perf_reporter.py --regression-check --tolerance 15
```

### 3. Cross-Language Comparison

```bash
# Compare Python vs PowerShell implementations
python benchmarks/perf_suite.py --cross-language

# Analyze historical cross-language performance
python tools/perf_reporter.py --compare python powershell --days 14
```

## Benchmarking Best Practices

### 1. Statistical Significance

**Minimum Requirements:**
- **Warmup iterations**: 100+ (accounts for JIT compilation, caching)
- **Measurement iterations**: 1000+ (statistical significance)
- **Multiple runs**: 3+ runs for variance detection
- **Percentile reporting**: Include p50, p95, p99 for latency distribution

```python
# ✅ Statistically significant benchmark
def benchmark_with_significance(func, iterations=1000, runs=3):
    all_results = []
    
    for run in range(runs):
        # Warmup
        for _ in range(100):
            func()
        
        # Measurement
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            times.append((time.perf_counter() - start) * 1_000_000)
        
        all_results.append({
            'mean_us': statistics.mean(times),
            'p95_us': sorted(times)[int(0.95 * len(times))],
            'std_us': statistics.stdev(times)
        })
    
    # Aggregate across runs
    return {
        'mean_us': statistics.mean([r['mean_us'] for r in all_results]),
        'p95_us': statistics.mean([r['p95_us'] for r in all_results]),
        'std_us': statistics.mean([r['std_us'] for r in all_results]),
        'run_variance': statistics.stdev([r['mean_us'] for r in all_results]),
        'confidence': 'high' if statistics.stdev([r['mean_us'] for r in all_results]) < 0.1 else 'low'
    }
```

### 2. Environment Consistency

**Control Variables:**
- System load (benchmark on idle system)
- Memory pressure (consistent available memory)
- Temperature (CPU throttling effects)
- Background processes (minimal interference)

```python
# Environment validation before benchmarking
def validate_benchmark_environment():
    """Validate system is suitable for benchmarking"""
    import psutil
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 20:
        print(f"⚠️ Warning: High CPU usage ({cpu_percent:.1f}%) may affect benchmark accuracy")
    
    # Check memory availability
    memory = psutil.virtual_memory()
    if memory.percent > 80:
        print(f"⚠️ Warning: High memory usage ({memory.percent:.1f}%) may affect benchmark accuracy")
    
    # Check for thermal throttling (if available)
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            max_temp = max(temp.current for sensors in temps.values() for temp in sensors)
            if max_temp > 80:
                print(f"⚠️ Warning: High CPU temperature ({max_temp}°C) may cause throttling")
    except:
        pass  # Temperature monitoring not available
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'suitable': cpu_percent < 20 and memory.percent < 80
    }
```

### 3. Test Data Realism

**Data Characteristics:**
- Realistic size distributions
- Representative complexity patterns
- Edge cases and boundary conditions
- Production-like data volumes

```python
def create_realistic_test_data(scenario: str = "production"):
    """Create test data that mirrors production characteristics"""
    
    scenarios = {
        'minimal': {
            'pattern_count': 100,
            'max_depth': 3,
            'wildcard_ratio': 0.1
        },
        'typical': {
            'pattern_count': 1000,
            'max_depth': 5,
            'wildcard_ratio': 0.3
        },
        'production': {
            'pattern_count': 10000,
            'max_depth': 8,
            'wildcard_ratio': 0.4
        },
        'stress': {
            'pattern_count': 100000,
            'max_depth': 12,
            'wildcard_ratio': 0.5
        }
    }
    
    config = scenarios.get(scenario, scenarios['typical'])
    
    patterns = {}
    
    # Generate patterns with realistic distribution
    for i in range(config['pattern_count']):
        depth = random.randint(1, config['max_depth'])
        
        # Create hierarchical pattern
        parts = [f"level{j}" for j in range(depth)]
        
        # Add wildcards based on ratio
        if random.random() < config['wildcard_ratio']:
            wildcard_pos = random.randint(0, len(parts) - 1)
            parts[wildcard_pos] = "*"
        
        pattern_key = ".".join(parts)
        patterns[pattern_key] = f"value_{i}"
    
    return patterns
```

## Benchmark Types and Use Cases

### 1. Micro-Benchmarks

**Purpose**: Test individual function performance
**Use Case**: Optimize specific algorithms or operations

```python
# Example: Benchmark individual pattern matching functions
def benchmark_pattern_matching():
    """Micro-benchmark for pattern matching optimization"""
    
    test_patterns = ["service.*", "api.v1.*", "data.*.config"]
    test_strings = ["service.auth", "api.v1.users", "data.cache.config"]
    
    implementations = {
        'regex_based': lambda patterns, strings: regex_match_implementation(patterns, strings),
        'fnmatch_based': lambda patterns, strings: fnmatch_implementation(patterns, strings),
        'optimized_hybrid': lambda patterns, strings: hybrid_implementation(patterns, strings)
    }
    
    runner = BenchmarkRunner()
    return runner.compare_implementations(implementations, (test_patterns, test_strings))
```

### 2. Integration Benchmarks

**Purpose**: Test component interaction performance
**Use Case**: Validate system-level performance

```python
# Example: Benchmark full compilation pipeline
def benchmark_compilation_pipeline():
    """Integration benchmark for full compilation process"""
    
    def full_pipeline_test():
        # Simulate full compilation workflow
        compiler = ConfigCompiler()
        patterns = create_realistic_test_data('typical')
        
        # Full pipeline: load -> compile -> expand -> output
        compiled = compiler.compile_patterns(patterns)
        expanded = list(compiler.expander.expand_pattern_stream(compiled))
        return len(expanded)
    
    runner = BenchmarkRunner()
    return runner.benchmark_function(full_pipeline_test, name="full_compilation_pipeline")
```

### 3. Stress Testing

**Purpose**: Test behavior under extreme load
**Use Case**: Validate scalability and stability

```python
def stress_test_large_datasets():
    """Stress test with progressively larger datasets"""
    
    sizes = [1000, 5000, 10000, 25000, 50000]
    results = {}
    
    for size in sizes:
        print(f"Stress testing with {size:,} patterns...")
        
        try:
            test_data = create_realistic_test_data('stress')
            test_data = dict(list(test_data.items())[:size])  # Limit to target size
            
            start_time = time.time()
            processed = process_large_dataset(test_data)
            end_time = time.time()
            
            results[size] = {
                'success': True,
                'duration_seconds': end_time - start_time,
                'throughput': len(processed) / (end_time - start_time),
                'memory_usage_mb': get_current_memory_usage()
            }
            
        except MemoryError:
            results[size] = {'success': False, 'error': 'memory_limit_exceeded'}
            break
        except Exception as e:
            results[size] = {'success': False, 'error': str(e)}
    
    return results
```

### 4. Regression Testing

**Purpose**: Detect performance degradation over time
**Use Case**: CI/CD pipeline integration

```python
def automated_regression_test():
    """Automated regression test for CI/CD"""
    
    # Core test functions
    test_functions = {
        'pattern_compilation': test_pattern_compilation_performance,
        'pattern_expansion': test_pattern_expansion_performance,
        'json_processing': test_json_processing_performance,
        'index_search': test_index_search_performance
    }
    
    # Run regression test
    tester = RegressionTester("benchmarks/results")
    results = tester.run_regression_test(test_functions, tolerance_pct=10.0)
    
    # Store results in database
    db = PerformanceDatabase()
    db.store_regression_result(
        benchmark_suite="core_regression",
        passed=results['regression_analysis']['passed'],
        regression_count=len(results['regression_analysis']['regressions']),
        improvement_count=len(results['regression_analysis']['improvements']),
        tolerance_percent=10.0,
        full_results=results
    )
    
    return results
```

## Performance Measurement Standards

### 1. Timing Precision

```python
# ✅ High precision timing
import time

def precise_timing_measurement():
    """Use highest precision timer available"""
    
    # perf_counter() provides highest precision
    start = time.perf_counter()
    operation_to_measure()
    end = time.perf_counter()
    
    return (end - start) * 1_000_000  # Convert to microseconds

# ❌ Low precision timing
def imprecise_timing():
    start = time.time()  # Lower precision
    operation_to_measure()
    return (time.time() - start) * 1000  # Milliseconds
```

### 2. Memory Measurement

```python
# ✅ Accurate memory measurement
def measure_memory_accurately():
    """Accurate memory measurement with GC control"""
    
    # Force garbage collection for consistent baseline
    gc.collect()
    
    try:
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        # Execute operation
        result = memory_intensive_operation()
        
        # Measure after operation
        memory_after = process.memory_info().rss
        memory_delta = memory_after - memory_before
        
        return {
            'result': result,
            'memory_delta_bytes': memory_delta,
            'memory_delta_mb': memory_delta / (1024 * 1024)
        }
        
    except ImportError:
        # Fallback method
        memory_before = sum(sys.getsizeof(obj) for obj in gc.get_objects())
        result = memory_intensive_operation()
        memory_after = sum(sys.getsizeof(obj) for obj in gc.get_objects())
        
        return {
            'result': result,
            'memory_delta_bytes': memory_after - memory_before,
            'memory_delta_mb': (memory_after - memory_before) / (1024 * 1024)
        }
```

### 3. PowerShell Measurement

```powershell
# ✅ Accurate PowerShell timing
function Measure-PreciseTiming {
    param(
        [scriptblock]$Operation,
        [int]$Iterations = 1000
    )
    
    # Use high-precision .NET stopwatch
    $timings = @()
    
    for ($i = 0; $i -lt $Iterations; $i++) {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        & $Operation | Out-Null
        $stopwatch.Stop()
        $timings += $stopwatch.Elapsed.TotalMicroseconds
    }
    
    return @{
        MeanMicroseconds = ($timings | Measure-Object -Average).Average
        MedianMicroseconds = ($timings | Sort-Object)[[math]::Floor($timings.Count / 2)]
        P95Microseconds = ($timings | Sort-Object)[[math]::Floor(0.95 * $timings.Count)]
    }
}
```

## Benchmark Configuration

### 1. Test Scenarios

```yaml
# benchmark_config.yaml
scenarios:
  unit_test:
    iterations: 10000
    warmup: 1000
    data_size: small
    focus: algorithm_optimization
    
  integration_test:
    iterations: 1000
    warmup: 100
    data_size: medium
    focus: component_interaction
    
  stress_test:
    iterations: 100
    warmup: 10
    data_size: large
    focus: scalability_limits
    
  production_simulation:
    iterations: 500
    warmup: 50
    data_size: realistic
    focus: user_experience

data_sizes:
  small: 100
  medium: 1000
  large: 10000
  realistic: 5000
  stress: 50000
```

### 2. Performance Thresholds

```python
# Performance requirements and thresholds
PERFORMANCE_THRESHOLDS = {
    'core_functions': {
        'pattern_compilation': {
            'max_time_us': 100,
            'min_throughput_ops': 1000,
            'max_memory_mb': 10
        },
        'pattern_expansion': {
            'max_time_us': 500,
            'min_throughput_ops': 500,
            'max_memory_mb': 20
        }
    },
    'scripts': {
        'secret_audit': {
            'max_time_ms': 5000,  # 5 second max for secret scanning
            'max_memory_mb': 100
        },
        'file_processing': {
            'max_time_ms': 1000,
            'max_memory_mb': 50
        }
    },
    'regression_tolerance': {
        'timing_degradation_pct': 10,
        'memory_increase_pct': 15,
        'throughput_decrease_pct': 10
    }
}

def validate_performance_requirements(metrics: Dict[str, Any], category: str, test_name: str) -> Dict[str, Any]:
    """Validate performance against defined requirements"""
    
    thresholds = PERFORMANCE_THRESHOLDS.get(category, {}).get(test_name, {})
    if not thresholds:
        return {'status': 'no_thresholds_defined'}
    
    violations = []
    
    # Check timing requirements
    if 'max_time_us' in thresholds and metrics.get('mean_us', 0) > thresholds['max_time_us']:
        violations.append({
            'metric': 'timing',
            'requirement': f"<{thresholds['max_time_us']}μs",
            'actual': f"{metrics['mean_us']:.1f}μs",
            'severity': 'high'
        })
    
    # Check throughput requirements
    if 'min_throughput_ops' in thresholds and metrics.get('ops_per_second', 0) < thresholds['min_throughput_ops']:
        violations.append({
            'metric': 'throughput',
            'requirement': f">{thresholds['min_throughput_ops']} ops/sec",
            'actual': f"{metrics['ops_per_second']:.0f} ops/sec",
            'severity': 'medium'
        })
    
    # Check memory requirements
    if 'max_memory_mb' in thresholds and metrics.get('memory_delta_mb', 0) > thresholds['max_memory_mb']:
        violations.append({
            'metric': 'memory',
            'requirement': f"<{thresholds['max_memory_mb']}MB",
            'actual': f"{metrics['memory_delta_mb']:.1f}MB",
            'severity': 'medium'
        })
    
    return {
        'status': 'passed' if not violations else 'failed',
        'violations': violations,
        'thresholds_checked': list(thresholds.keys())
    }
```

## Advanced Benchmarking Techniques

### 1. Comparative Analysis

```python
class AdvancedComparator:
    """Advanced comparison with statistical significance testing"""
    
    def __init__(self):
        self.significance_threshold = 0.05  # p-value for statistical significance
    
    def compare_with_significance(
        self, 
        implementation_a: Callable,
        implementation_b: Callable,
        test_data: Any,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Compare implementations with statistical significance testing"""
        
        # Collect multiple samples for each implementation
        samples_a = self._collect_samples(implementation_a, test_data, iterations, runs=5)
        samples_b = self._collect_samples(implementation_b, test_data, iterations, runs=5)
        
        # Statistical testing
        from scipy.stats import ttest_ind
        
        t_stat, p_value = ttest_ind(samples_a, samples_b)
        
        mean_a = statistics.mean(samples_a)
        mean_b = statistics.mean(samples_b)
        
        return {
            'implementation_a_mean_us': mean_a,
            'implementation_b_mean_us': mean_b,
            'performance_difference_pct': abs(mean_a - mean_b) / min(mean_a, mean_b) * 100,
            'faster_implementation': 'a' if mean_a < mean_b else 'b',
            'statistical_significance': {
                't_statistic': t_stat,
                'p_value': p_value,
                'is_significant': p_value < self.significance_threshold,
                'confidence_level': (1 - p_value) * 100 if p_value < 1 else 0
            },
            'recommendation': self._generate_significance_recommendation(mean_a, mean_b, p_value)
        }
    
    def _collect_samples(self, func: Callable, test_data: Any, iterations: int, runs: int) -> List[float]:
        """Collect multiple independent samples"""
        samples = []
        
        for run in range(runs):
            # Warmup
            for _ in range(100):
                func(test_data)
            
            # Single run measurement
            start = time.perf_counter()
            for _ in range(iterations):
                func(test_data)
            end = time.perf_counter()
            
            # Average time per operation in microseconds
            avg_time_us = (end - start) / iterations * 1_000_000
            samples.append(avg_time_us)
        
        return samples
    
    def _generate_significance_recommendation(self, mean_a: float, mean_b: float, p_value: float) -> str:
        """Generate recommendation based on statistical significance"""
        
        faster = 'A' if mean_a < mean_b else 'B'
        difference_pct = abs(mean_a - mean_b) / min(mean_a, mean_b) * 100
        
        if p_value < 0.01:
            return f"Strong evidence: Implementation {faster} is significantly faster ({difference_pct:.1f}% improvement)"
        elif p_value < 0.05:
            return f"Moderate evidence: Implementation {faster} appears faster ({difference_pct:.1f}% improvement)"
        else:
            return f"No significant difference detected (p={p_value:.3f}) - choose based on other factors"
```

### 2. Performance Profiling Integration

```python
import cProfile
import pstats
from functools import wraps

def profile_benchmark(func):
    """Decorator to add profiling to benchmark functions"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        
        # Run with profiling
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        # Generate profile report
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Save profile data
        profile_file = f"benchmarks/profiles/{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.prof"
        Path(profile_file).parent.mkdir(exist_ok=True)
        stats.dump_stats(profile_file)
        
        # Add profile summary to result
        if isinstance(result, dict):
            result['profile_file'] = profile_file
            result['top_functions'] = get_top_functions_from_stats(stats)
        
        return result
    
    return wrapper

def get_top_functions_from_stats(stats: pstats.Stats, count: int = 5) -> List[Dict[str, Any]]:
    """Extract top functions from profile stats"""
    
    top_functions = []
    
    # Get stats as list
    stats_list = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        stats_list.append({
            'function': f"{func[0]}:{func[1]}({func[2]})",
            'calls': cc,
            'total_time': tt,
            'cumulative_time': ct,
            'time_per_call': tt / cc if cc > 0 else 0
        })
    
    # Sort by total time and take top N
    stats_list.sort(key=lambda x: x['total_time'], reverse=True)
    
    return stats_list[:count]
```

## Continuous Performance Monitoring

### 1. CI/CD Integration

```yaml
# .github/workflows/performance-monitoring.yml
name: Performance Monitoring

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance-regression:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install psutil pandas matplotlib scipy
    
    - name: Run performance regression test
      run: |
        python benchmarks/perf_suite.py --regression-test
      env:
        SR_BENCH_MIN_RATIO: 30
        SR_BENCH_MAX_P95_US: 100
    
    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmarks/results/
    
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      run: |
        python tools/perf_reporter.py --analyze --benchmark comprehensive_suite --days 1
```

### 2. Automated Alerting

```python
class PerformanceAlertSystem:
    """Automated alerting for performance issues"""
    
    def __init__(self, alert_thresholds: Dict[str, float]):
        self.thresholds = alert_thresholds
        self.alert_history = []
    
    def check_for_alerts(self, recent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check recent results for alert conditions"""
        
        alerts = []
        
        for test_name, metrics in recent_results.items():
            if 'error' in metrics:
                alerts.append({
                    'severity': 'high',
                    'type': 'test_failure',
                    'test': test_name,
                    'message': f"Test {test_name} failed: {metrics['error']}"
                })
                continue
            
            # Check timing alerts
            if metrics.get('mean_us', 0) > self.thresholds.get('max_time_us', float('inf')):
                alerts.append({
                    'severity': 'medium',
                    'type': 'timing_threshold',
                    'test': test_name,
                    'message': f"Timing threshold exceeded: {metrics['mean_us']:.1f}μs > {self.thresholds['max_time_us']}μs"
                })
            
            # Check memory alerts
            if metrics.get('memory_delta_mb', 0) > self.thresholds.get('max_memory_mb', float('inf')):
                alerts.append({
                    'severity': 'medium',
                    'type': 'memory_threshold',
                    'test': test_name,
                    'message': f"Memory threshold exceeded: {metrics['memory_delta_mb']:.1f}MB > {self.thresholds['max_memory_mb']}MB"
                })
            
            # Check throughput alerts
            if metrics.get('ops_per_second', float('inf')) < self.thresholds.get('min_throughput', 0):
                alerts.append({
                    'severity': 'low',
                    'type': 'throughput_threshold',
                    'test': test_name,
                    'message': f"Throughput below threshold: {metrics['ops_per_second']:.0f} < {self.thresholds['min_throughput']} ops/sec"
                })
        
        # Store alert history
        if alerts:
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'alerts': alerts
            })
        
        return alerts
    
    def send_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Send alerts via configured channels"""
        
        if not alerts:
            return
        
        # Group by severity
        high_severity = [a for a in alerts if a['severity'] == 'high']
        medium_severity = [a for a in alerts if a['severity'] == 'medium']
        low_severity = [a for a in alerts if a['severity'] == 'low']
        
        # Format alert message
        message = f"🚨 Performance Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if high_severity:
            message += f"🔴 HIGH SEVERITY ({len(high_severity)}):\n"
            for alert in high_severity:
                message += f"  - {alert['message']}\n"
            message += "\n"
        
        if medium_severity:
            message += f"🟡 MEDIUM SEVERITY ({len(medium_severity)}):\n"
            for alert in medium_severity:
                message += f"  - {alert['message']}\n"
            message += "\n"
        
        if low_severity:
            message += f"🟢 LOW SEVERITY ({len(low_severity)}):\n"
            for alert in low_severity:
                message += f"  - {alert['message']}\n"
        
        # Send via configured channels (console, file, webhook, etc.)
        print(message)
        
        # Log to file
        alert_log = Path("benchmarks/alerts.log")
        with open(alert_log, 'a') as f:
            f.write(f"\n{message}\n" + "=" * 80 + "\n")
```

## Benchmark Templates

### 1. Function Benchmark Template

```python
# Template for benchmarking individual functions
def benchmark_template_function():
    """Template for creating function benchmarks"""
    
    # 1. Setup
    runner = BenchmarkRunner(warmup_iterations=100, measurement_iterations=1000)
    
    # 2. Define function to test
    def function_under_test(data):
        # Your function implementation
        return process_data(data)
    
    # 3. Create test data
    test_data = create_test_data_for_function()
    
    # 4. Run benchmark
    results = runner.benchmark_function(function_under_test, test_data)
    
    # 5. Validate against requirements
    validation = validate_performance_requirements(results, 'core_functions', 'your_function')
    
    # 6. Store results
    db = PerformanceDatabase()
    db.store_benchmark_results('your_benchmark', 'python', results)
    
    return results, validation
```

### 2. Comparison Benchmark Template

```python
def benchmark_template_comparison():
    """Template for comparing multiple implementations"""
    
    # 1. Define implementations to compare
    implementations = {
        'naive_approach': lambda data: naive_implementation(data),
        'optimized_approach': lambda data: optimized_implementation(data),
        'alternative_approach': lambda data: alternative_implementation(data)
    }
    
    # 2. Create test data
    test_data = create_realistic_test_data('typical')
    
    # 3. Run comparison
    comparator = ComparisonBenchmark(BenchmarkRunner())
    results = comparator.compare_implementations(implementations, test_data)
    
    # 4. Analyze and report
    print_comparison_results(results)
    
    # 5. Store results
    db = PerformanceDatabase()
    db.store_benchmark_results('implementation_comparison', 'python', results)
    
    return results
```

### 3. PowerShell Benchmark Template

```powershell
# Template for PowerShell function benchmarking
function Benchmark-Template {
    param([scriptblock]$FunctionToTest, [hashtable]$TestData)
    
    # 1. Configuration
    $iterations = 1000
    $warmupIterations = 100
    
    # 2. Run benchmark
    $results = Measure-FunctionPerformance -Function $FunctionToTest -Parameters $TestData -Iterations $iterations -WarmupIterations $warmupIterations
    
    # 3. Validate results
    $validation = Test-PerformanceRequirements $results
    
    # 4. Export results
    $outputFile = "benchmarks/results/powershell_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $results | ConvertTo-Json -Depth 5 | Out-File $outputFile -Encoding UTF8
    
    # 5. Display summary
    Write-Host "Benchmark Results:" -ForegroundColor Cyan
    Write-Host "  Mean time: $($results.MeanMicroseconds.ToString('F2'))μs" -ForegroundColor White
    Write-Host "  Throughput: $($results.OperationsPerSecond) ops/sec" -ForegroundColor White
    Write-Host "  Performance class: $($results.PerformanceClass)" -ForegroundColor White
    
    return $results
}
```

## Usage Examples

### 1. Benchmark Specific Module

```bash
# Benchmark the core compiler module
python benchmarks/perf_suite.py --module core.compiler --size 5000 --iterations 2000

# Results will include:
# - Individual function timings
# - Memory usage analysis  
# - Performance classification
# - Recommendations for optimization
```

### 2. Run Regression Suite

```bash
# Run complete regression test suite
python benchmarks/perf_suite.py --regression-test

# PowerShell regression test
pwsh scripts/perf_analyzer.ps1 -RegressionTest

# Check regression status
python tools/perf_reporter.py --regression-check --tolerance 15
```

### 3. Historical Analysis

```bash
# Analyze performance trends over 60 days
python tools/perf_reporter.py --analyze --benchmark pattern_compilation --days 60

# Generate comprehensive HTML report
python tools/perf_reporter.py --report --format html --days 30

# Compare languages over time
python tools/perf_reporter.py --compare python powershell --days 14
```

## Integration with Existing Tools

The benchmarking framework integrates seamlessly with existing Strataregula performance tools:

### 1. bench_guard.py Integration

```python
# Enhanced bench_guard with framework integration
def enhanced_bench_guard():
    """Enhanced version that integrates with performance database"""
    
    # Run existing bench_guard logic
    from bench_guard import main as original_bench_guard
    
    # Capture results
    results = original_bench_guard()
    
    # Store in performance database
    db = PerformanceDatabase()
    db.store_benchmark_results('bench_guard_regression', 'python', results)
    
    return results
```

### 2. Pattern Benchmark Integration

```python
# Integration with existing pattern_benchmark.py
def integrate_pattern_benchmarks():
    """Integrate existing pattern benchmarks into framework"""
    
    from benchmarks.pattern_benchmark import benchmark_patterns
    
    # Run existing benchmarks
    pattern_results = benchmark_patterns()
    
    # Convert to framework format and store
    db = PerformanceDatabase()
    formatted_results = {'functions': pattern_results}
    db.store_benchmark_results('micro_patterns', 'python', formatted_results)
    
    return pattern_results
```

### 3. Performance Test Integration

```python
# Integration with existing test_performance.py
def integrate_performance_tests():
    """Integrate existing performance tests"""
    
    from idea.dev.test_performance import run_performance_validation
    
    # Run existing validation
    validation_results = run_performance_validation()
    
    # Store comprehensive results
    db = PerformanceDatabase()
    db.store_benchmark_results('performance_validation', 'python', {
        'validation_passed': validation_results,
        'timestamp': datetime.now().isoformat()
    })
    
    return validation_results
```

## Best Practices Summary

### Development Workflow
1. **Measure before optimizing** - Establish baseline performance
2. **Use appropriate benchmark type** - Micro vs integration vs stress
3. **Control environment variables** - Consistent testing conditions
4. **Validate statistical significance** - Ensure meaningful comparisons
5. **Track historical trends** - Monitor for regressions over time

### Benchmark Design
1. **Realistic test data** - Mirror production characteristics
2. **Sufficient iterations** - Achieve statistical significance
3. **Proper warmup** - Account for JIT and caching effects
4. **Multiple metrics** - Timing, memory, throughput
5. **Error handling** - Graceful failure and recovery

### Results Management
1. **Structured storage** - Consistent format and metadata
2. **Historical tracking** - Trend analysis and regression detection
3. **Automated reporting** - Regular performance health checks
4. **Alert systems** - Proactive issue detection
5. **Cross-language comparison** - Optimize technology choices

The benchmarking framework provides a comprehensive foundation for maintaining and improving Strataregula's performance across all components and languages.
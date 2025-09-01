# Performance Regression Detection

## Overview
Automated performance regression detection system for continuous monitoring and early detection of performance degradation in Strataregula components.

## Regression Detection Strategy

### 1. Multi-Level Detection

```
Level 1: Function-Level Regression
├── Individual function performance tracking
├── Statistical significance testing
└── Automated baseline management

Level 2: Component-Level Regression  
├── Module interaction performance
├── Integration test performance
└── End-to-end workflow timing

Level 3: System-Level Regression
├── Overall system throughput
├── Resource utilization patterns
└── User experience metrics
```

### 2. Detection Methodology

#### Statistical Approach

```python
import statistics
from scipy import stats
from typing import List, Dict, Any, Tuple

class StatisticalRegressionDetector:
    """Statistical approach to regression detection"""
    
    def __init__(self, confidence_level: float = 0.95, practical_threshold: float = 10.0):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        self.practical_threshold = practical_threshold  # Minimum meaningful change %
    
    def detect_regression(
        self, 
        baseline_samples: List[float], 
        current_samples: List[float]
    ) -> Dict[str, Any]:
        """
        Detect performance regression using statistical testing.
        
        Returns comprehensive analysis including:
        - Statistical significance (t-test)
        - Practical significance (effect size)
        - Confidence intervals
        - Regression severity classification
        """
        
        if len(baseline_samples) < 10 or len(current_samples) < 10:
            return {'error': 'Insufficient samples for statistical analysis (minimum 10 per group)'}
        
        # Descriptive statistics
        baseline_mean = statistics.mean(baseline_samples)
        current_mean = statistics.mean(current_samples)
        baseline_std = statistics.stdev(baseline_samples)
        current_std = statistics.stdev(current_samples)
        
        # Effect size (percentage change)
        effect_size_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
        
        # Statistical significance test
        try:
            t_stat, p_value = stats.ttest_ind(current_samples, baseline_samples)
            is_statistically_significant = p_value < self.alpha
            
            # Cohen's d (standardized effect size)
            pooled_std = statistics.sqrt(((len(baseline_samples) - 1) * baseline_std**2 + 
                                        (len(current_samples) - 1) * current_std**2) / 
                                       (len(baseline_samples) + len(current_samples) - 2))
            cohens_d = (current_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0
            
        except Exception as e:
            return {'error': f'Statistical test failed: {e}'}
        
        # Practical significance
        is_practically_significant = abs(effect_size_pct) >= self.practical_threshold
        
        # Regression classification
        regression_severity = self._classify_regression_severity(
            effect_size_pct, is_statistically_significant, is_practically_significant
        )
        
        # Confidence intervals
        confidence_interval = self._calculate_confidence_interval(
            current_samples, self.confidence_level
        )
        
        return {
            'regression_detected': effect_size_pct > 0 and is_statistically_significant and is_practically_significant,
            'effect_size_percent': effect_size_pct,
            'statistical_analysis': {
                'p_value': p_value,
                't_statistic': t_stat,
                'is_significant': is_statistically_significant,
                'cohens_d': cohens_d,
                'effect_size_interpretation': self._interpret_effect_size(cohens_d)
            },
            'practical_analysis': {
                'is_practically_significant': is_practically_significant,
                'threshold_percent': self.practical_threshold,
                'severity': regression_severity
            },
            'performance_comparison': {
                'baseline_mean_us': baseline_mean,
                'current_mean_us': current_mean,
                'baseline_std_us': baseline_std,
                'current_std_us': current_std,
                'confidence_interval_us': confidence_interval
            },
            'recommendation': self._generate_regression_recommendation(regression_severity, effect_size_pct)
        }
    
    def _classify_regression_severity(
        self, 
        effect_size_pct: float, 
        statistically_significant: bool, 
        practically_significant: bool
    ) -> str:
        """Classify regression severity"""
        
        if not statistically_significant or effect_size_pct <= 0:
            return "none"
        
        if not practically_significant:
            return "negligible"
        
        if effect_size_pct > 50:
            return "critical"
        elif effect_size_pct > 25:
            return "major"
        elif effect_size_pct > 10:
            return "moderate"
        else:
            return "minor"
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(cohens_d)
        
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def _calculate_confidence_interval(self, samples: List[float], confidence: float) -> Tuple[float, float]:
        """Calculate confidence interval for performance measurements"""
        
        mean = statistics.mean(samples)
        std_err = statistics.stdev(samples) / statistics.sqrt(len(samples))
        
        # t-distribution critical value (approximation for large samples)
        t_critical = 1.96 if confidence == 0.95 else 2.58 if confidence == 0.99 else 1.645
        
        margin_of_error = t_critical * std_err
        
        return (mean - margin_of_error, mean + margin_of_error)
    
    def _generate_regression_recommendation(self, severity: str, effect_size_pct: float) -> str:
        """Generate actionable recommendation based on regression analysis"""
        
        recommendations = {
            "critical": f"🚨 IMMEDIATE ACTION REQUIRED: {effect_size_pct:.1f}% performance degradation detected",
            "major": f"🔴 HIGH PRIORITY: Investigate {effect_size_pct:.1f}% performance regression",
            "moderate": f"🟡 MEDIUM PRIORITY: Monitor and address {effect_size_pct:.1f}% performance decline",
            "minor": f"🟢 LOW PRIORITY: Minor {effect_size_pct:.1f}% performance regression detected",
            "negligible": f"✅ NO ACTION: Statistically significant but practically negligible change",
            "none": f"✅ NO REGRESSION: Performance within expected variance"
        }
        
        return recommendations.get(severity, "Unknown regression severity")
```

### 3. Adaptive Baseline Management

```python
class AdaptiveBaselineManager:
    """Manages performance baselines with automatic adaptation"""
    
    def __init__(self, baseline_file: str, adaptation_strategy: str = "conservative"):
        self.baseline_file = Path(baseline_file)
        self.adaptation_strategy = adaptation_strategy
        self.baseline_data = self._load_baseline()
        
        # Adaptation parameters
        self.adaptation_configs = {
            'conservative': {
                'min_samples': 20,
                'confidence_threshold': 0.99,
                'improvement_threshold': 15.0  # Must be 15% better to update baseline
            },
            'moderate': {
                'min_samples': 10,
                'confidence_threshold': 0.95,
                'improvement_threshold': 10.0
            },
            'aggressive': {
                'min_samples': 5,
                'confidence_threshold': 0.90,
                'improvement_threshold': 5.0
            }
        }
    
    def should_update_baseline(
        self, 
        test_name: str, 
        recent_results: List[float]
    ) -> Dict[str, Any]:
        """Determine if baseline should be updated based on recent performance"""
        
        config = self.adaptation_configs[self.adaptation_strategy]
        
        if len(recent_results) < config['min_samples']:
            return {
                'should_update': False,
                'reason': f'Insufficient samples ({len(recent_results)} < {config["min_samples"]})'
            }
        
        if test_name not in self.baseline_data:
            return {
                'should_update': True,
                'reason': 'No existing baseline - establishing new baseline'
            }
        
        baseline_mean = self.baseline_data[test_name]['mean_us']
        recent_mean = statistics.mean(recent_results)
        
        # Check for consistent improvement
        improvement_pct = ((baseline_mean - recent_mean) / baseline_mean) * 100
        
        if improvement_pct < config['improvement_threshold']:
            return {
                'should_update': False,
                'reason': f'Improvement {improvement_pct:.1f}% < threshold {config["improvement_threshold"]}%'
            }
        
        # Statistical significance test
        baseline_samples = self.baseline_data[test_name].get('samples', [baseline_mean] * 10)
        
        detector = StatisticalRegressionDetector(confidence_level=config['confidence_threshold'])
        analysis = detector.detect_regression(recent_results, baseline_samples)  # Note: reversed for improvement
        
        if analysis.get('error'):
            return {
                'should_update': False,
                'reason': f'Statistical analysis failed: {analysis["error"]}'
            }
        
        is_significant_improvement = (
            analysis['statistical_analysis']['is_significant'] and 
            analysis['effect_size_percent'] < -config['improvement_threshold']  # Negative = improvement
        )
        
        return {
            'should_update': is_significant_improvement,
            'reason': f'Significant improvement detected: {abs(analysis["effect_size_percent"]):.1f}%',
            'statistical_confidence': analysis['statistical_analysis']['p_value'],
            'improvement_percent': abs(analysis['effect_size_percent'])
        }
    
    def update_baseline(self, test_name: str, new_samples: List[float], metadata: Dict[str, Any] = None) -> None:
        """Update baseline with new performance data"""
        
        new_baseline = {
            'mean_us': statistics.mean(new_samples),
            'std_us': statistics.stdev(new_samples) if len(new_samples) > 1 else 0,
            'samples': new_samples[-10:],  # Keep last 10 samples for future comparison
            'updated_at': datetime.now().isoformat(),
            'sample_count': len(new_samples),
            'metadata': metadata or {}
        }
        
        self.baseline_data[test_name] = new_baseline
        self._save_baseline()
        
        print(f"✅ Updated baseline for {test_name}: {new_baseline['mean_us']:.2f}μs")
    
    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline data from file"""
        if self.baseline_file.exists():
            try:
                return json.loads(self.baseline_file.read_text())
            except Exception as e:
                print(f"Warning: Could not load baseline from {self.baseline_file}: {e}")
        
        return {}
    
    def _save_baseline(self) -> None:
        """Save baseline data to file"""
        self.baseline_file.parent.mkdir(exist_ok=True)
        self.baseline_file.write_text(json.dumps(self.baseline_data, indent=2))
```

## Automated Regression Testing

### 1. CI/CD Integration

```python
class ContinuousRegressionTester:
    """Continuous regression testing for CI/CD pipelines"""
    
    def __init__(self, config_file: str = "performance_config.yaml"):
        self.config = self._load_config(config_file)
        self.baseline_manager = AdaptiveBaselineManager(
            "benchmarks/baselines/ci_baseline.json",
            adaptation_strategy=self.config.get('adaptation_strategy', 'moderate')
        )
        self.detector = StatisticalRegressionDetector(
            confidence_level=self.config.get('confidence_level', 0.95),
            practical_threshold=self.config.get('practical_threshold', 10.0)
        )
    
    def run_ci_regression_test(self) -> Dict[str, Any]:
        """Run regression test suitable for CI/CD pipeline"""
        
        # Quick test suite for CI (reduced iterations for speed)
        test_suite = self._get_ci_test_suite()
        
        print("🔍 Running CI performance regression test...")
        
        # Execute tests
        current_results = {}
        for test_name, test_func in test_suite.items():
            print(f"  Testing {test_name}...")
            
            # Reduced iterations for CI speed
            iterations = self.config.get('ci_iterations', 100)
            
            # Quick benchmark
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                test_func()
                times.append((time.perf_counter() - start) * 1_000_000)
            
            current_results[test_name] = {
                'mean_us': statistics.mean(times),
                'p95_us': sorted(times)[int(0.95 * len(times))],
                'samples': times[-10:]  # Keep recent samples
            }
        
        # Compare against baseline
        regression_results = self._analyze_ci_regressions(current_results)
        
        # Update baselines if appropriate
        self._update_baselines_if_improved(current_results)
        
        return {
            'ci_test_results': current_results,
            'regression_analysis': regression_results,
            'passed': regression_results['overall_status'] != 'regression_detected',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_ci_test_suite(self) -> Dict[str, Callable]:
        """Get optimized test suite for CI execution"""
        
        return {
            'core_compilation': lambda: self._test_core_compilation_ci(),
            'pattern_matching': lambda: self._test_pattern_matching_ci(),
            'file_processing': lambda: self._test_file_processing_ci(),
            'json_parsing': lambda: self._test_json_parsing_ci()
        }
    
    def _test_core_compilation_ci(self):
        """Quick core compilation test for CI"""
        from strataregula.core.compiler import PatternCompiler
        compiler = PatternCompiler()
        
        # Small but representative test case
        patterns = {f"svc.{i}.cfg": f"val_{i}" for i in range(100)}
        return len(list(compiler.compile_patterns(patterns)))
    
    def _analyze_ci_regressions(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze regressions with CI-appropriate thresholds"""
        
        regressions = []
        improvements = []
        
        for test_name, current_metrics in current_results.items():
            if test_name not in self.baseline_manager.baseline_data:
                continue  # No baseline to compare against
            
            baseline_metrics = self.baseline_manager.baseline_data[test_name]
            baseline_samples = baseline_metrics.get('samples', [baseline_metrics['mean_us']] * 10)
            current_samples = current_metrics['samples']
            
            # Run statistical detection
            detection_result = self.detector.detect_regression(baseline_samples, current_samples)
            
            if detection_result.get('regression_detected'):
                regressions.append({
                    'test_name': test_name,
                    'effect_size_pct': detection_result['effect_size_percent'],
                    'p_value': detection_result['statistical_analysis']['p_value'],
                    'severity': detection_result['practical_analysis']['severity']
                })
            
            elif detection_result['effect_size_percent'] < -5:  # 5% improvement
                improvements.append({
                    'test_name': test_name,
                    'improvement_pct': abs(detection_result['effect_size_percent']),
                    'p_value': detection_result['statistical_analysis']['p_value']
                })
        
        # Overall status determination
        critical_regressions = [r for r in regressions if r['severity'] in ['critical', 'major']]
        
        if critical_regressions:
            overall_status = 'regression_detected'
        elif regressions:
            overall_status = 'minor_regressions'
        else:
            overall_status = 'no_regressions'
        
        return {
            'overall_status': overall_status,
            'regressions': regressions,
            'improvements': improvements,
            'critical_regressions': critical_regressions,
            'recommendation': self._generate_ci_recommendation(overall_status, critical_regressions)
        }
    
    def _generate_ci_recommendation(self, status: str, critical_regressions: List[Dict]) -> str:
        """Generate CI-specific recommendation"""
        
        if status == 'regression_detected':
            critical_tests = [r['test_name'] for r in critical_regressions]
            return f"❌ FAIL CI: Critical regressions in {', '.join(critical_tests)}"
        
        elif status == 'minor_regressions':
            return "⚠️ WARN: Minor regressions detected - monitor closely"
        
        else:
            return "✅ PASS: No performance regressions detected"
```

### 2. Automated Alerting System

```python
class PerformanceAlertSystem:
    """Automated alerting for performance regressions"""
    
    def __init__(self, alert_config: Dict[str, Any]):
        self.config = alert_config
        self.alert_channels = self._initialize_alert_channels()
        self.alert_history = []
    
    def process_regression_results(self, regression_results: Dict[str, Any]) -> None:
        """Process regression results and send alerts if needed"""
        
        alerts = self._generate_alerts(regression_results)
        
        if alerts:
            self._send_alerts(alerts)
            self._record_alert_history(alerts)
    
    def _generate_alerts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on regression results"""
        
        alerts = []
        analysis = results.get('regression_analysis', {})
        
        # Critical regression alerts
        critical_regressions = analysis.get('critical_regressions', [])
        for regression in critical_regressions:
            alerts.append({
                'severity': 'critical',
                'type': 'performance_regression',
                'title': f"Critical Performance Regression: {regression['test_name']}",
                'message': f"Performance degraded by {regression['effect_size_pct']:.1f}% (p={regression['p_value']:.4f})",
                'action_required': True,
                'test_name': regression['test_name']
            })
        
        # Major regression alerts
        major_regressions = [r for r in analysis.get('regressions', []) if r['severity'] == 'major']
        for regression in major_regressions:
            alerts.append({
                'severity': 'high',
                'type': 'performance_regression',
                'title': f"Major Performance Regression: {regression['test_name']}",
                'message': f"Performance degraded by {regression['effect_size_pct']:.1f}%",
                'action_required': True,
                'test_name': regression['test_name']
            })
        
        # Performance improvement notifications
        improvements = analysis.get('improvements', [])
        significant_improvements = [i for i in improvements if i['improvement_pct'] > 20]
        
        if significant_improvements:
            improvement_tests = [i['test_name'] for i in significant_improvements]
            alerts.append({
                'severity': 'info',
                'type': 'performance_improvement',
                'title': 'Significant Performance Improvements Detected',
                'message': f"Performance improved in: {', '.join(improvement_tests)}",
                'action_required': False
            })
        
        return alerts
    
    def _send_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Send alerts through configured channels"""
        
        for alert in alerts:
            severity = alert['severity']
            
            # Console output (always enabled)
            self._send_console_alert(alert)
            
            # File logging
            if 'file' in self.alert_channels:
                self._send_file_alert(alert)
            
            # Email alerts for critical issues
            if severity == 'critical' and 'email' in self.alert_channels:
                self._send_email_alert(alert)
            
            # Webhook for integration with monitoring systems
            if 'webhook' in self.alert_channels:
                self._send_webhook_alert(alert)
    
    def _send_console_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to console"""
        
        severity_icons = {
            'critical': '🚨',
            'high': '🔴', 
            'medium': '🟡',
            'low': '🟢',
            'info': 'ℹ️'
        }
        
        icon = severity_icons.get(alert['severity'], '❓')
        print(f"{icon} {alert['title']}")
        print(f"   {alert['message']}")
        
        if alert.get('action_required'):
            print(f"   ⚡ ACTION REQUIRED: Investigate {alert['test_name']} performance regression")
    
    def _send_file_alert(self, alert: Dict[str, Any]) -> None:
        """Log alert to file"""
        
        log_file = Path(self.config.get('alert_log_file', 'benchmarks/alerts.log'))
        log_file.parent.mkdir(exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {alert['severity'].upper()}: {alert['title']} - {alert['message']}\n"
        
        with open(log_file, 'a') as f:
            f.write(log_entry)
    
    def _record_alert_history(self, alerts: List[Dict[str, Any]]) -> None:
        """Record alerts in history for trend analysis"""
        
        self.alert_history.append({
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'alert_count': len(alerts),
            'critical_count': sum(1 for a in alerts if a['severity'] == 'critical'),
            'high_count': sum(1 for a in alerts if a['severity'] == 'high')
        })
        
        # Keep only recent history (last 100 entries)
        self.alert_history = self.alert_history[-100:]
    
    def get_alert_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze alert trends over time"""
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_time.isoformat()
        
        recent_alerts = [
            entry for entry in self.alert_history
            if entry['timestamp'] >= cutoff_iso
        ]
        
        if not recent_alerts:
            return {'status': 'no_recent_alerts'}
        
        # Trend analysis
        total_alerts = sum(entry['alert_count'] for entry in recent_alerts)
        critical_alerts = sum(entry['critical_count'] for entry in recent_alerts)
        
        # Alert frequency analysis
        alert_frequency = len(recent_alerts) / days  # Alerts per day
        
        return {
            'analysis_period_days': days,
            'total_alert_events': len(recent_alerts),
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'alert_frequency_per_day': alert_frequency,
            'trend': self._classify_alert_trend(recent_alerts),
            'health_assessment': self._assess_alert_health(alert_frequency, critical_alerts)
        }
    
    def _classify_alert_trend(self, recent_alerts: List[Dict]) -> str:
        """Classify alert trend over time"""
        
        if len(recent_alerts) < 3:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid_point = len(recent_alerts) // 2
        first_half_rate = sum(entry['alert_count'] for entry in recent_alerts[:mid_point]) / mid_point
        second_half_rate = sum(entry['alert_count'] for entry in recent_alerts[mid_point:]) / (len(recent_alerts) - mid_point)
        
        if second_half_rate > first_half_rate * 1.5:
            return "worsening"
        elif second_half_rate < first_half_rate * 0.7:
            return "improving"
        else:
            return "stable"
```

## PowerShell Regression Detection

### 1. PowerShell-Specific Regression Testing

```powershell
# PowerShell regression detection framework
function Test-PowerShellPerformanceRegression {
    param(
        [string]$BaselineFile = "benchmarks/baselines/powershell_baseline.json",
        [double]$TolerancePercent = 10.0,
        [int]$MinSamples = 10
    )
    
    Write-Host "🔍 PowerShell Performance Regression Detection" -ForegroundColor Cyan
    
    # Load baseline data
    $baseline = @{}
    if (Test-Path $BaselineFile) {
        try {
            $baseline = Get-Content $BaselineFile | ConvertFrom-Json -AsHashtable
            Write-Host "✅ Loaded baseline with $($baseline.Count) test results" -ForegroundColor Green
        }
        catch {
            Write-Warning "Failed to load baseline: $($_.Exception.Message)"
        }
    }
    
    # Define test suite
    $testSuite = Get-RegressionTestSuite
    
    # Execute current tests
    $currentResults = @{}
    foreach ($testName in $testSuite.Keys) {
        Write-Host "  Testing: $testName" -ForegroundColor Yellow
        
        # Collect multiple samples for statistical analysis
        $samples = @()
        for ($i = 0; $i -lt $MinSamples; $i++) {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            & $testSuite[$testName] | Out-Null
            $stopwatch.Stop()
            $samples += $stopwatch.Elapsed.TotalMicroseconds
        }
        
        $currentResults[$testName] = @{
            MeanMicroseconds = ($samples | Measure-Object -Average).Average
            P95Microseconds = ($samples | Sort-Object)[[math]::Floor(0.95 * $samples.Count)]
            Samples = $samples
            SampleCount = $samples.Count
        }
    }
    
    # Analyze regressions
    $regressionAnalysis = Compare-PowerShellBaseline -Current $currentResults -Baseline $baseline -TolerancePercent $TolerancePercent
    
    # Generate comprehensive report
    $regressionReport = @{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        BaselineFile = $BaselineFile
        TolerancePercent = $TolerancePercent
        CurrentResults = $currentResults
        RegressionAnalysis = $regressionAnalysis
        SystemInfo = Get-PowerShellSystemInfo
        TestConfiguration = @{
            MinSamples = $MinSamples
            TestSuite = @($testSuite.Keys)
        }
    }
    
    # Save results
    $reportFile = "benchmarks/results/powershell_regression_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $regressionReport | ConvertTo-Json -Depth 10 | Out-File $reportFile -Encoding UTF8
    
    # Display results
    Show-RegressionResults $regressionAnalysis
    
    return $regressionReport
}

function Compare-PowerShellBaseline {
    param(
        [hashtable]$Current,
        [hashtable]$Baseline,
        [double]$TolerancePercent
    )
    
    $regressions = @()
    $improvements = @()
    $toleranceFactor = 1 + ($TolerancePercent / 100)
    
    foreach ($testName in $Current.Keys) {
        if (-not $Baseline.ContainsKey($testName)) {
            continue
        }
        
        $currentMean = $Current[$testName].MeanMicroseconds
        $baselineMean = $Baseline[$testName].MeanMicroseconds
        
        # Simple regression detection (can be enhanced with statistical testing)
        if ($currentMean -gt ($baselineMean * $toleranceFactor)) {
            $degradationPct = (($currentMean - $baselineMean) / $baselineMean) * 100
            
            $regressions += @{
                TestName = $testName
                BaselineMicroseconds = $baselineMean
                CurrentMicroseconds = $currentMean
                DegradationPercent = $degradationPct
                Severity = Get-RegressionSeverity $degradationPct
            }
        }
        elseif ($currentMean -lt ($baselineMean * 0.9)) {  # 10% improvement threshold
            $improvementPct = (($baselineMean - $currentMean) / $baselineMean) * 100
            
            $improvements += @{
                TestName = $testName
                BaselineMicroseconds = $baselineMean
                CurrentMicroseconds = $currentMean
                ImprovementPercent = $improvementPct
            }
        }
    }
    
    return @{
        Passed = ($regressions.Count -eq 0)
        TotalTests = $Current.Count
        BaselineTests = $Baseline.Count
        Regressions = $regressions
        Improvements = $improvements
        CriticalRegressions = @($regressions | Where-Object { $_.Severity -eq 'critical' })
        Summary = @{
            RegressionCount = $regressions.Count
            ImprovementCount = $improvements.Count
            CriticalRegressionCount = @($regressions | Where-Object { $_.Severity -eq 'critical' }).Count
        }
    }
}

function Get-RegressionSeverity {
    param([double]$DegradationPercent)
    
    if ($DegradationPercent -gt 50) { return "critical" }
    elseif ($DegradationPercent -gt 25) { return "major" }
    elseif ($DegradationPercent -gt 10) { return "moderate" }
    else { return "minor" }
}

function Show-RegressionResults {
    param([hashtable]$Analysis)
    
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "POWERSHELL REGRESSION ANALYSIS RESULTS" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    if ($Analysis.Passed) {
        Write-Host "✅ PASSED: No performance regressions detected" -ForegroundColor Green
    }
    else {
        Write-Host "❌ FAILED: Performance regressions detected" -ForegroundColor Red
    }
    
    $summary = $Analysis.Summary
    Write-Host "`nSummary:" -ForegroundColor White
    Write-Host "  Total tests: $($Analysis.TotalTests)" -ForegroundColor White
    Write-Host "  Regressions: $($summary.RegressionCount)" -ForegroundColor $(if ($summary.RegressionCount -gt 0) { "Red" } else { "Green" })
    Write-Host "  Improvements: $($summary.ImprovementCount)" -ForegroundColor $(if ($summary.ImprovementCount -gt 0) { "Green" } else { "White" })
    Write-Host "  Critical: $($summary.CriticalRegressionCount)" -ForegroundColor $(if ($summary.CriticalRegressionCount -gt 0) { "Red" } else { "Green" })
    
    if ($Analysis.Regressions.Count -gt 0) {
        Write-Host "`n🚨 Detected Regressions:" -ForegroundColor Red
        
        foreach ($regression in $Analysis.Regressions) {
            $severityColor = switch ($regression.Severity) {
                "critical" { "Red" }
                "major" { "DarkRed" }
                "moderate" { "Yellow" }
                default { "DarkYellow" }
            }
            
            Write-Host "  $($regression.TestName):" -ForegroundColor $severityColor
            Write-Host "    Baseline: $($regression.BaselineMicroseconds.ToString('F2'))μs" -ForegroundColor Gray
            Write-Host "    Current:  $($regression.CurrentMicroseconds.ToString('F2'))μs" -ForegroundColor Gray
            Write-Host "    Degradation: $($regression.DegradationPercent.ToString('F1'))% ($($regression.Severity))" -ForegroundColor $severityColor
        }
    }
    
    if ($Analysis.Improvements.Count -gt 0) {
        Write-Host "`n🚀 Performance Improvements:" -ForegroundColor Green
        
        foreach ($improvement in $Analysis.Improvements) {
            Write-Host "  $($improvement.TestName): $($improvement.ImprovementPercent.ToString('F1'))% faster" -ForegroundColor Green
        }
    }
}

function Get-RegressionTestSuite {
    """PowerShell regression test suite"""
    
    return @{
        "string_operations" = {
            # Test string processing performance
            $strings = 1..1000 | ForEach-Object { "test_string_$_" }
            $result = $strings -join ","
            return $result.Length
        }
        
        "file_filtering" = {
            # Test file filtering logic from secret-audit.ps1
            $testFiles = 1..500 | ForEach-Object { 
                @{
                    FullName = "C:\test\file_$_.txt"
                    Length = Get-Random -Minimum 1000 -Maximum 1000000
                    Extension = if ($_ % 4 -eq 0) { ".exe" } else { ".txt" }
                }
            }
            
            $filtered = $testFiles | Where-Object { 
                $_.Length -le 2000000 -and $_.Extension -eq ".txt" 
            }
            
            return $filtered.Count
        }
        
        "regex_matching" = {
            # Test regex compilation and matching
            $patterns = @('test_\d+', 'file_[a-z]+', 'data_.{1,10}')
            $testStrings = 1..300 | ForEach-Object { "test_$_", "file_abc", "data_xyz" } | Get-Random -Count 200
            
            $matchCount = 0
            foreach ($pattern in $patterns) {
                $regex = [regex]::new($pattern)
                foreach ($str in $testStrings) {
                    if ($regex.IsMatch($str)) {
                        $matchCount++
                    }
                }
            }
            
            return $matchCount
        }
        
        "collection_operations" = {
            # Test PowerShell collection performance
            $list = [System.Collections.ArrayList]::new()
            for ($i = 0; $i -lt 1000; $i++) {
                [void]$list.Add("item_$i")
            }
            
            $filtered = $list | Where-Object { $_ -like "*5*" }
            return $filtered.Count
        }
    }
}

function Get-PowerShellSystemInfo {
    """Get PowerShell system information for regression context"""
    
    return @{
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        Platform = $PSVersionTable.Platform
        OS = $PSVersionTable.OS
        Edition = $PSVersionTable.PSEdition
        ProcessorCount = [Environment]::ProcessorCount
        WorkingSet = [math]::Round((Get-Process -Id $PID).WorkingSet64 / 1MB, 2)
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
}
```

## Regression Prevention Strategies

### 1. Proactive Performance Gates

```python
class PerformanceGate:
    """Performance gate for preventing regressions in development"""
    
    def __init__(self, performance_requirements: Dict[str, Dict[str, float]]):
        self.requirements = performance_requirements
        self.gate_history = []
    
    def validate_before_merge(self, pr_performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance before allowing merge"""
        
        validation_results = {
            'gate_passed': True,
            'violations': [],
            'warnings': [],
            'performance_summary': {},
            'recommendation': 'APPROVE'
        }
        
        for component, metrics in pr_performance_data.items():
            if component in self.requirements:
                requirements = self.requirements[component]
                violations = self._check_component_requirements(component, metrics, requirements)
                
                if violations:
                    validation_results['violations'].extend(violations)
                    validation_results['gate_passed'] = False
                
                # Check for warning conditions (approaching limits)
                warnings = self._check_warning_conditions(component, metrics, requirements)
                validation_results['warnings'].extend(warnings)
        
        # Determine final recommendation
        if not validation_results['gate_passed']:
            validation_results['recommendation'] = 'BLOCK_MERGE'
        elif validation_results['warnings']:
            validation_results['recommendation'] = 'APPROVE_WITH_WARNINGS'
        
        # Record gate result
        self.gate_history.append({
            'timestamp': datetime.now().isoformat(),
            'passed': validation_results['gate_passed'],
            'violations': len(validation_results['violations']),
            'warnings': len(validation_results['warnings'])
        })
        
        return validation_results
    
    def _check_component_requirements(
        self, 
        component: str, 
        metrics: Dict[str, float], 
        requirements: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Check component against performance requirements"""
        
        violations = []
        
        # Check timing requirements
        if 'max_time_us' in requirements:
            actual_time = metrics.get('mean_us', 0)
            if actual_time > requirements['max_time_us']:
                violations.append({
                    'component': component,
                    'metric': 'timing',
                    'requirement': f"<{requirements['max_time_us']}μs",
                    'actual': f"{actual_time:.1f}μs",
                    'severity': 'blocking',
                    'overage_pct': ((actual_time - requirements['max_time_us']) / requirements['max_time_us']) * 100
                })
        
        # Check throughput requirements
        if 'min_throughput' in requirements:
            actual_throughput = metrics.get('ops_per_second', 0)
            if actual_throughput < requirements['min_throughput']:
                violations.append({
                    'component': component,
                    'metric': 'throughput',
                    'requirement': f">{requirements['min_throughput']} ops/sec",
                    'actual': f"{actual_throughput:.0f} ops/sec",
                    'severity': 'blocking',
                    'shortfall_pct': ((requirements['min_throughput'] - actual_throughput) / requirements['min_throughput']) * 100
                })
        
        # Check memory requirements
        if 'max_memory_mb' in requirements:
            actual_memory = metrics.get('memory_delta_mb', 0)
            if actual_memory > requirements['max_memory_mb']:
                violations.append({
                    'component': component,
                    'metric': 'memory',
                    'requirement': f"<{requirements['max_memory_mb']}MB",
                    'actual': f"{actual_memory:.1f}MB", 
                    'severity': 'blocking',
                    'overage_pct': ((actual_memory - requirements['max_memory_mb']) / requirements['max_memory_mb']) * 100
                })
        
        return violations
    
    def _check_warning_conditions(
        self, 
        component: str, 
        metrics: Dict[str, float], 
        requirements: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Check for warning conditions (approaching limits)"""
        
        warnings = []
        warning_threshold = 0.8  # 80% of limit triggers warning
        
        # Timing warnings
        if 'max_time_us' in requirements:
            actual_time = metrics.get('mean_us', 0)
            warning_limit = requirements['max_time_us'] * warning_threshold
            
            if actual_time > warning_limit:
                warnings.append({
                    'component': component,
                    'metric': 'timing',
                    'message': f"Approaching timing limit: {actual_time:.1f}μs (limit: {requirements['max_time_us']}μs)",
                    'usage_pct': (actual_time / requirements['max_time_us']) * 100
                })
        
        # Memory warnings
        if 'max_memory_mb' in requirements:
            actual_memory = metrics.get('memory_delta_mb', 0)
            warning_limit = requirements['max_memory_mb'] * warning_threshold
            
            if actual_memory > warning_limit:
                warnings.append({
                    'component': component,
                    'metric': 'memory',
                    'message': f"Approaching memory limit: {actual_memory:.1f}MB (limit: {requirements['max_memory_mb']}MB)",
                    'usage_pct': (actual_memory / requirements['max_memory_mb']) * 100
                })
        
        return warnings
```

### 2. Early Warning System

```python
class EarlyWarningSystem:
    """Early warning system for gradual performance degradation"""
    
    def __init__(self, lookback_days: int = 14, degradation_threshold: float = 2.0):
        self.lookback_days = lookback_days
        self.degradation_threshold = degradation_threshold  # % per day
        self.warning_history = []
    
    def check_gradual_degradation(self, db: PerformanceDatabase) -> Dict[str, Any]:
        """Check for gradual performance degradation over time"""
        
        # Get recent performance data
        cutoff_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                SELECT benchmark_name, test_name, timestamp, mean_time_us
                FROM benchmark_runs 
                WHERE timestamp >= ?
                ORDER BY benchmark_name, test_name, timestamp
            """, (cutoff_date,))
            
            data = cursor.fetchall()
        
        # Group by benchmark and test
        test_groups = {}
        for row in data:
            key = f"{row[0]}.{row[1]}"
            if key not in test_groups:
                test_groups[key] = []
            
            test_groups[key].append({
                'timestamp': datetime.fromisoformat(row[2]),
                'mean_time_us': row[3]
            })
        
        # Analyze each test for gradual degradation
        warnings = []
        
        for test_key, test_data in test_groups.items():
            if len(test_data) < 5:  # Need minimum data points
                continue
            
            degradation_analysis = self._analyze_gradual_degradation(test_data)
            
            if degradation_analysis['degradation_rate_pct_per_day'] > self.degradation_threshold:
                warnings.append({
                    'test': test_key,
                    'degradation_rate': degradation_analysis['degradation_rate_pct_per_day'],
                    'projected_impact': degradation_analysis['projected_30_day_impact'],
                    'confidence': degradation_analysis['trend_confidence'],
                    'severity': self._classify_degradation_severity(degradation_analysis['degradation_rate_pct_per_day'])
                })
        
        return {
            'analysis_period_days': self.lookback_days,
            'tests_analyzed': len(test_groups),
            'gradual_degradation_warnings': warnings,
            'overall_health': 'concerning' if len(warnings) > 3 else 'good' if len(warnings) == 0 else 'monitoring',
            'recommendations': self._generate_early_warning_recommendations(warnings)
        }
    
    def _analyze_gradual_degradation(self, test_data: List[Dict]) -> Dict[str, Any]:
        """Analyze gradual performance degradation for single test"""
        
        # Sort by timestamp
        sorted_data = sorted(test_data, key=lambda x: x['timestamp'])
        
        # Calculate daily degradation rate using linear regression
        days_from_start = [(entry['timestamp'] - sorted_data[0]['timestamp']).days for entry in sorted_data]
        performance_values = [entry['mean_time_us'] for entry in sorted_data]
        
        # Simple linear regression
        n = len(days_from_start)
        if n < 2:
            return {'degradation_rate_pct_per_day': 0, 'trend_confidence': 'insufficient_data'}
        
        x_mean = statistics.mean(days_from_start)
        y_mean = statistics.mean(performance_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(days_from_start, performance_values))
        denominator = sum((x - x_mean) ** 2 for x in days_from_start)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Convert slope to percentage degradation per day
        baseline_performance = performance_values[0]
        degradation_rate_pct_per_day = (slope / baseline_performance) * 100 if baseline_performance > 0 else 0
        
        # Calculate trend confidence based on R²
        y_pred = [slope * x + (y_mean - slope * x_mean) for x in days_from_start]
        ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(performance_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in performance_values)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        trend_confidence = 'high' if r_squared > 0.8 else 'medium' if r_squared > 0.5 else 'low'
        
        # Project future impact
        projected_30_day_impact = degradation_rate_pct_per_day * 30
        
        return {
            'degradation_rate_pct_per_day': degradation_rate_pct_per_day,
            'trend_confidence': trend_confidence,
            'r_squared': r_squared,
            'projected_30_day_impact': projected_30_day_impact,
            'data_points': n,
            'analysis_period_days': max(days_from_start)
        }
    
    def _classify_degradation_severity(self, degradation_rate_per_day: float) -> str:
        """Classify severity of gradual degradation"""
        
        if degradation_rate_per_day > 10:
            return "critical"  # >10% per day = 300% per month
        elif degradation_rate_per_day > 5:
            return "high"      # >5% per day = 150% per month
        elif degradation_rate_per_day > 2:
            return "medium"    # >2% per day = 60% per month
        else:
            return "low"       # <2% per day = <60% per month
    
    def _generate_early_warning_recommendations(self, warnings: List[Dict]) -> List[str]:
        """Generate recommendations for early warning results"""
        
        if not warnings:
            return ["✅ No gradual performance degradation detected"]
        
        recommendations = []
        
        critical_warnings = [w for w in warnings if w['severity'] == 'critical']
        if critical_warnings:
            critical_tests = [w['test'] for w in critical_warnings]
            recommendations.append(f"🚨 URGENT: Investigate critical degradation in {', '.join(critical_tests)}")
        
        high_warnings = [w for w in warnings if w['severity'] == 'high']
        if high_warnings:
            high_tests = [w['test'] for w in high_warnings]
            recommendations.append(f"🔴 HIGH PRIORITY: Address degradation trends in {', '.join(high_tests)}")
        
        # General recommendations
        if len(warnings) > 5:
            recommendations.append("📊 SYSTEMATIC ISSUE: Multiple degradation trends suggest systemic performance issues")
        
        if any(w['confidence'] == 'high' for w in warnings):
            recommendations.append("🔍 RELIABLE DATA: High-confidence degradation trends require immediate attention")
        
        return recommendations
```

## Integration with Existing Tools

### 1. Enhanced bench_guard.py Integration

```python
# Enhanced version of existing bench_guard.py with regression detection
def enhanced_bench_guard_with_regression():
    """Enhanced bench_guard with comprehensive regression detection"""
    
    # Run original bench_guard logic
    from bench_guard import main as original_bench_guard
    
    # Capture detailed results
    results = original_bench_guard()
    
    # Add regression detection
    detector = StatisticalRegressionDetector()
    baseline_manager = AdaptiveBaselineManager("benchmarks/bench_guard_baseline.json")
    
    # Enhanced analysis
    if results.get('passed'):
        # Check if this represents a significant improvement
        current_ratio = results['comparison']['ratio_fast_over_slow']
        
        if 'bench_guard_ratio' in baseline_manager.baseline_data:
            baseline_ratio = baseline_manager.baseline_data['bench_guard_ratio']['mean_ratio']
            
            improvement_pct = ((current_ratio - baseline_ratio) / baseline_ratio) * 100
            
            if improvement_pct > 20:  # Significant improvement
                should_update = baseline_manager.should_update_baseline(
                    'bench_guard_ratio',
                    [current_ratio] * 10  # Simulate samples
                )
                
                if should_update['should_update']:
                    baseline_manager.update_baseline(
                        'bench_guard_ratio',
                        [current_ratio] * 10,
                        {'improvement_pct': improvement_pct}
                    )
    
    return results

# Integration with existing pattern_benchmark.py
def enhanced_pattern_benchmark_with_regression():
    """Enhanced pattern benchmark with regression detection"""
    
    from benchmarks.pattern_benchmark import benchmark_patterns
    
    # Run existing benchmarks
    pattern_results = benchmark_patterns()
    
    # Add regression analysis
    db = PerformanceDatabase()
    
    # Store results in new format
    formatted_results = {'functions': pattern_results}
    db.store_benchmark_results('micro_patterns', 'python', formatted_results)
    
    # Check for regressions
    analyzer = TrendAnalyzer(db)
    trend_analysis = analyzer.analyze_performance_trends('micro_patterns', days=30)
    
    # Enhanced reporting
    print("\n" + "="*60)
    print("ENHANCED PATTERN BENCHMARK WITH REGRESSION ANALYSIS")
    print("="*60)
    
    if 'error' not in trend_analysis:
        summary = trend_analysis['trend_summary']
        print(f"Performance Health: {summary['health_status'].upper()}")
        print(f"Degrading Tests: {summary['degrading_tests']}")
        print(f"Improving Tests: {summary['improving_tests']}")
        
        for recommendation in summary['recommendations']:
            print(f"💡 {recommendation}")
    
    return pattern_results, trend_analysis
```

## Regression Testing Automation

### 1. GitHub Actions Integration

```yaml
# .github/workflows/performance-regression.yml
name: Performance Regression Detection

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 4 * * *'  # Daily at 4 AM

jobs:
  performance-regression:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -e .
        pip install psutil pandas matplotlib scipy
        
    - name: Setup PowerShell
      uses: azure/powershell@v1
      with:
        azPSVersion: 'latest'
        
    - name: Run Python regression tests
      run: |
        python benchmarks/perf_suite.py --regression-test
      env:
        PERFORMANCE_MODE: ci
        
    - name: Run PowerShell regression tests  
      run: |
        pwsh scripts/perf_analyzer.ps1 -RegressionTest
        
    - name: Analyze regression results
      run: |
        python tools/perf_reporter.py --regression-check --tolerance 10
        
    - name: Generate performance report
      if: always()
      run: |
        python tools/perf_reporter.py --report --format html --days 7
        
    - name: Upload benchmark artifacts
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: performance-results
        path: |
          benchmarks/results/
          benchmarks/reports/
          
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          
          // Read regression test results
          const pythonResults = JSON.parse(fs.readFileSync('benchmarks/results/regression_test_latest.json'));
          const powershellResults = JSON.parse(fs.readFileSync('benchmarks/results/powershell_regression_latest.json'));
          
          // Generate PR comment
          let comment = '## 📊 Performance Regression Test Results\n\n';
          
          // Python results
          const pythonPassed = pythonResults.regression_analysis.passed;
          comment += `### Python Tests: ${pythonPassed ? '✅ PASSED' : '❌ FAILED'}\n`;
          
          if (!pythonPassed) {
            const regressions = pythonResults.regression_analysis.regressions;
            comment += `- Regressions detected: ${regressions.length}\n`;
            regressions.forEach(reg => {
              comment += `  - ${reg.test} (${reg.metric}): ${reg.degradation_pct.toFixed(1)}% slower\n`;
            });
          }
          
          // PowerShell results  
          const powershellPassed = powershellResults.RegressionAnalysis.Passed;
          comment += `\n### PowerShell Tests: ${powershellPassed ? '✅ PASSED' : '❌ FAILED'}\n`;
          
          if (!powershellPassed) {
            const psRegressions = powershellResults.RegressionAnalysis.Regressions;
            comment += `- Regressions detected: ${psRegressions.length}\n`;
            psRegressions.forEach(reg => {
              comment += `  - ${reg.TestName}: ${reg.DegradationPercent.toFixed(1)}% slower\n`;
            });
          }
          
          // Overall recommendation
          const overallPassed = pythonPassed && powershellPassed;
          comment += `\n### Overall Status: ${overallPassed ? '✅ SAFE TO MERGE' : '❌ PERFORMANCE ISSUES DETECTED'}\n`;
          
          if (!overallPassed) {
            comment += '\n⚠️ Please address performance regressions before merging.\n';
          }
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
          
    - name: Fail on regression
      if: failure()
      run: exit 1
```

### 2. Local Development Integration

```python
# Git pre-commit hook for performance validation
def create_precommit_performance_hook():
    """Create git pre-commit hook for performance validation"""
    
    hook_content = '''#!/usr/bin/env python3
"""
Pre-commit performance validation hook
Runs quick performance checks before allowing commit
"""

import sys
import subprocess
from pathlib import Path

def run_quick_performance_check():
    """Run abbreviated performance check suitable for pre-commit"""
    
    print("🔍 Running pre-commit performance check...")
    
    # Quick Python performance test (reduced iterations)
    try:
        result = subprocess.run([
            sys.executable, 
            "benchmarks/perf_suite.py", 
            "--regression-test",
            "--iterations", "100"  # Quick test
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print("❌ Python performance regression detected")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Performance test timed out - allowing commit")
        return True
    except Exception as e:
        print(f"⚠️ Performance test error: {e} - allowing commit")
        return True
    
    # Quick PowerShell test (if available)
    try:
        ps_result = subprocess.run([
            "pwsh", 
            "scripts/perf_analyzer.ps1", 
            "-RegressionTest",
            "-Iterations", "50"  # Very quick test
        ], capture_output=True, text=True, timeout=30)
        
        if ps_result.returncode != 0:
            print("❌ PowerShell performance regression detected")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # PowerShell not available or timed out - allow commit
        pass
    
    print("✅ Pre-commit performance check passed")
    return True

if __name__ == "__main__":
    if not run_quick_performance_check():
        print("\\n🚨 Commit blocked due to performance regression")
        print("Run full performance analysis: python benchmarks/perf_suite.py --regression-test")
        sys.exit(1)
    
    sys.exit(0)
'''
    
    # Install hook
    hook_file = Path(".git/hooks/pre-commit")
    hook_file.write_text(hook_content)
    hook_file.chmod(0o755)  # Make executable
    
    print(f"✅ Performance pre-commit hook installed: {hook_file}")
```

## Regression Detection Configuration

### 1. Configuration Management

```yaml
# performance_config.yaml
regression_detection:
  # Statistical parameters
  confidence_level: 0.95
  practical_threshold_percent: 10.0
  minimum_samples: 20
  
  # Baseline management
  baseline_adaptation: "moderate"  # conservative, moderate, aggressive
  improvement_threshold_percent: 15.0
  
  # Alert thresholds
  alert_thresholds:
    critical_degradation_percent: 50
    major_degradation_percent: 25
    moderate_degradation_percent: 10
    
  # Early warning system
  gradual_degradation:
    lookback_days: 14
    degradation_rate_threshold_percent_per_day: 2.0
    
  # CI/CD specific settings
  ci_mode:
    reduced_iterations: 100
    timeout_seconds: 300
    quick_test_only: true

# Performance requirements by component
performance_requirements:
  core_functions:
    pattern_compilation:
      max_time_us: 100
      min_throughput_ops: 1000
      max_memory_mb: 10
      
    pattern_expansion:
      max_time_us: 500
      min_throughput_ops: 500
      max_memory_mb: 20
      
    json_processing:
      max_time_us: 200
      min_throughput_ops: 800
      max_memory_mb: 15
      
  scripts:
    secret_audit:
      max_time_ms: 5000
      max_memory_mb: 100
      
    file_processing:
      max_time_ms: 1000
      max_memory_mb: 50

# Test data configurations
test_data_configs:
  minimal:
    size: 100
    complexity: low
    
  typical:
    size: 1000  
    complexity: medium
    
  production:
    size: 10000
    complexity: high
    
  stress:
    size: 100000
    complexity: maximum
```

### 2. Configuration Loading

```python
import yaml
from typing import Dict, Any

class PerformanceConfig:
    """Load and manage performance configuration"""
    
    def __init__(self, config_file: str = "performance_config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        
        if not self.config_file.exists():
            # Create default configuration
            default_config = self._get_default_config()
            self.config_file.write_text(yaml.dump(default_config, default_flow_style=False))
            print(f"✅ Created default performance configuration: {self.config_file}")
            return default_config
        
        try:
            return yaml.safe_load(self.config_file.read_text())
        except Exception as e:
            print(f"⚠️ Error loading config from {self.config_file}: {e}")
            return self._get_default_config()
    
    def get_regression_config(self) -> Dict[str, Any]:
        """Get regression detection configuration"""
        return self.config.get('regression_detection', {})
    
    def get_performance_requirements(self, category: str = None) -> Dict[str, Any]:
        """Get performance requirements for category"""
        requirements = self.config.get('performance_requirements', {})
        
        if category:
            return requirements.get(category, {})
        
        return requirements
    
    def get_test_data_config(self, scenario: str = 'typical') -> Dict[str, Any]:
        """Get test data configuration for scenario"""
        return self.config.get('test_data_configs', {}).get(scenario, {'size': 1000, 'complexity': 'medium'})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            'regression_detection': {
                'confidence_level': 0.95,
                'practical_threshold_percent': 10.0,
                'minimum_samples': 20,
                'baseline_adaptation': 'moderate'
            },
            'performance_requirements': {
                'core_functions': {
                    'pattern_compilation': {
                        'max_time_us': 100,
                        'min_throughput_ops': 1000,
                        'max_memory_mb': 10
                    }
                }
            },
            'test_data_configs': {
                'typical': {'size': 1000, 'complexity': 'medium'}
            }
        }
```

## Usage Examples

### 1. Comprehensive Regression Test

```bash
# Run complete regression test suite
python benchmarks/perf_suite.py --regression-test

# Analysis and reporting
python tools/perf_reporter.py --regression-check --tolerance 10

# Generate trends report
python tools/perf_reporter.py --analyze --days 30
```

### 2. PowerShell Regression Testing

```powershell
# Run PowerShell regression tests
.\scripts\perf_analyzer.ps1 -RegressionTest

# Compare with specific tolerance
.\scripts\perf_analyzer.ps1 -RegressionTest -TolerancePercent 15

# Memory-focused analysis
.\scripts\perf_analyzer.ps1 -MemoryAnalysis
```

### 3. Early Warning Checks

```python
# Check for gradual degradation
from tools.perf_reporter import PerformanceDatabase, EarlyWarningSystem

db = PerformanceDatabase()
warning_system = EarlyWarningSystem(lookback_days=21, degradation_threshold=1.5)

warnings = warning_system.check_gradual_degradation(db)

if warnings['gradual_degradation_warnings']:
    print("⚠️ Gradual performance degradation detected")
    for warning in warnings['gradual_degradation_warnings']:
        print(f"  {warning['test']}: {warning['degradation_rate']:.2f}% per day")
```

### 4. Performance Gate Validation

```python
# Validate performance before merge (for PR automation)
from tools.perf_reporter import PerformanceGate

# Define requirements
requirements = {
    'pattern_compilation': {
        'max_time_us': 150,
        'min_throughput': 800,
        'max_memory_mb': 15
    }
}

gate = PerformanceGate(requirements)

# Run current performance tests
current_performance = run_current_performance_tests()

# Validate against gate
gate_result = gate.validate_before_merge(current_performance)

if gate_result['gate_passed']:
    print("✅ Performance gate PASSED - safe to merge")
else:
    print("❌ Performance gate FAILED")
    for violation in gate_result['violations']:
        print(f"  🚨 {violation['component']}: {violation['message']}")
    
    exit(1)
```

## Best Practices for Regression Detection

### 1. Baseline Management
- **Establish baselines early** in development cycle
- **Update baselines carefully** only after validated improvements
- **Version baselines** with code releases for correlation
- **Archive historical baselines** for long-term trend analysis

### 2. Test Design
- **Representative workloads** that mirror production usage
- **Consistent test environments** to reduce noise
- **Sufficient sample sizes** for statistical significance
- **Multiple metrics** beyond just timing (memory, throughput, etc.)

### 3. Alert Management
- **Tiered alerting** based on regression severity
- **Alert fatigue prevention** through proper thresholds
- **Actionable alerts** with specific remediation guidance
- **Alert trend analysis** to identify systemic issues

### 4. Integration Strategy
- **CI/CD integration** for automated detection
- **Pre-commit hooks** for early detection
- **Dashboard visualization** for ongoing monitoring
- **Historical tracking** for trend analysis

The regression detection system provides comprehensive protection against performance degradation while supporting continuous optimization and improvement of Strataregula components.
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PowerShell Performance Analyzer for Strataregula

.DESCRIPTION
    Comprehensive PowerShell performance analysis tool that provides:
    - Function-level performance benchmarking
    - Script execution profiling
    - Memory usage analysis
    - Cross-script performance comparison
    - Integration with Python benchmarking results

.PARAMETER ScriptPath
    Path to PowerShell script to analyze

.PARAMETER Function
    Specific function to benchmark

.PARAMETER Iterations
    Number of benchmark iterations (default: 1000)

.PARAMETER Compare
    Compare multiple implementations

.PARAMETER RegressionTest
    Run regression testing against baseline

.PARAMETER OutputDir
    Directory for results output (default: benchmarks/results)

.EXAMPLE
    .\perf_analyzer.ps1 -ScriptPath "secret-audit.ps1" -Iterations 500
    .\perf_analyzer.ps1 -Function "Should-ExcludeFile" -Compare
    .\perf_analyzer.ps1 -RegressionTest
#>

param(
    [string]$ScriptPath,
    [string]$Function,
    [int]$Iterations = 1000,
    [int]$WarmupIterations = 100,
    [switch]$Compare,
    [switch]$RegressionTest,
    [string]$OutputDir = "benchmarks/results",
    [switch]$Verbose,
    [switch]$MemoryAnalysis,
    [string]$TestDataSize = "medium"
)

# Ensure output directory exists
$outputPath = [System.IO.Path]::GetFullPath($OutputDir)
if (-not (Test-Path $outputPath)) {
    New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
}

# Core benchmarking functions
function Measure-FunctionPerformance {
    <#
    .SYNOPSIS
        Benchmark a PowerShell function with comprehensive metrics
    #>
    param(
        [scriptblock]$Function,
        [hashtable]$Parameters = @{},
        [int]$Iterations = 1000,
        [int]$WarmupIterations = 100,
        [string]$FunctionName = "anonymous"
    )
    
    Write-Host "Benchmarking function: $FunctionName" -ForegroundColor Cyan
    
    # Memory baseline
    [System.GC]::Collect()
    $memoryBefore = [System.GC]::GetTotalMemory($false)
    
    # Warmup phase
    Write-Verbose "Running warmup ($WarmupIterations iterations)..."
    for ($i = 0; $i -lt $WarmupIterations; $i++) {
        try {
            & $Function @Parameters | Out-Null
        }
        catch {
            return @{
                Function = $FunctionName
                Error = "Warmup failed: $($_.Exception.Message)"
            }
        }
    }
    
    # Measurement phase
    Write-Verbose "Running measurements ($Iterations iterations)..."
    $timings = @()
    $errorCount = 0
    
    for ($i = 0; $i -lt $Iterations; $i++) {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        try {
            $result = & $Function @Parameters
            $stopwatch.Stop()
            $timings += $stopwatch.Elapsed.TotalMicroseconds
        }
        catch {
            $stopwatch.Stop()
            $errorCount++
            if ($errorCount -gt ($Iterations * 0.05)) {  # More than 5% errors
                return @{
                    Function = $FunctionName
                    Error = "Too many execution errors: $($_.Exception.Message)"
                }
            }
        }
    }
    
    # Memory measurement
    [System.GC]::Collect()
    $memoryAfter = [System.GC]::GetTotalMemory($false)
    $memoryDelta = $memoryAfter - $memoryBefore
    
    # Statistical analysis
    if ($timings.Count -eq 0) {
        return @{
            Function = $FunctionName
            Error = "No successful measurements"
        }
    }
    
    $sortedTimings = $timings | Sort-Object
    $n = $sortedTimings.Count
    $mean = ($timings | Measure-Object -Average).Average
    $median = $sortedTimings[[math]::Floor($n / 2)]
    $p95 = $sortedTimings[[math]::Floor(0.95 * $n)]
    $p99 = $sortedTimings[[math]::Floor(0.99 * $n)]
    $stdDev = [math]::Sqrt(($timings | ForEach-Object { [math]::Pow($_ - $mean, 2) } | Measure-Object -Sum).Sum / $timings.Count)
    
    return @{
        Function = $FunctionName
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Iterations = $Iterations
        ErrorCount = $errorCount
        
        # Timing metrics (microseconds)
        MeanMicroseconds = $mean
        MedianMicroseconds = $median
        P95Microseconds = $p95
        P99Microseconds = $p99
        MinMicroseconds = $sortedTimings[0]
        MaxMicroseconds = $sortedTimings[-1]
        StandardDeviationMicroseconds = $stdDev
        
        # Throughput
        OperationsPerSecond = [math]::Round(1000000 / $mean)
        
        # Memory metrics
        MemoryDeltaBytes = $memoryDelta
        MemoryDeltaMB = [math]::Round($memoryDelta / 1MB, 3)
        MemoryPerOperationBytes = [math]::Round($memoryDelta / $Iterations, 2)
        
        # Performance classification
        PerformanceClass = Get-PerformanceClassification $mean
        
        # Variability analysis
        CoefficientOfVariation = if ($mean -gt 0) { $stdDev / $mean } else { 0 }
        Reliability = Get-ReliabilityRating ($stdDev / $mean)
    }
}

function Get-PerformanceClassification {
    param([double]$MeanTimeMicroseconds)
    
    if ($MeanTimeMicroseconds -lt 10) { return "excellent" }
    elseif ($MeanTimeMicroseconds -lt 100) { return "good" }
    elseif ($MeanTimeMicroseconds -lt 1000) { return "acceptable" }
    elseif ($MeanTimeMicroseconds -lt 10000) { return "slow" }
    else { return "very_slow" }
}

function Get-ReliabilityRating {
    param([double]$CoefficientOfVariation)
    
    if ($CoefficientOfVariation -lt 0.05) { return "very_reliable" }
    elseif ($CoefficientOfVariation -lt 0.1) { return "reliable" }
    elseif ($CoefficientOfVariation -lt 0.2) { return "moderate" }
    else { return "unreliable" }
}

function Measure-ScriptPerformance {
    <#
    .SYNOPSIS
        Benchmark an entire PowerShell script
    #>
    param(
        [string]$ScriptPath,
        [hashtable]$ScriptParameters = @{},
        [int]$Iterations = 10  # Fewer iterations for full scripts
    )
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Error "Script not found: $ScriptPath"
        return $null
    }
    
    Write-Host "Benchmarking script: $ScriptPath" -ForegroundColor Cyan
    
    $timings = @()
    $errorCount = 0
    
    # Warmup
    Write-Verbose "Script warmup..."
    try {
        & $ScriptPath @ScriptParameters | Out-Null
    }
    catch {
        Write-Warning "Script warmup failed: $($_.Exception.Message)"
    }
    
    # Measurements
    for ($i = 0; $i -lt $Iterations; $i++) {
        Write-Progress -Activity "Benchmarking Script" -Status "Iteration $($i + 1)/$Iterations" -PercentComplete (($i + 1) / $Iterations * 100)
        
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        try {
            & $ScriptPath @ScriptParameters | Out-Null
            $stopwatch.Stop()
            $timings += $stopwatch.Elapsed.TotalMilliseconds
        }
        catch {
            $stopwatch.Stop()
            $errorCount++
            Write-Verbose "Script execution error: $($_.Exception.Message)"
        }
    }
    
    Write-Progress -Activity "Benchmarking Script" -Completed
    
    if ($timings.Count -eq 0) {
        return @{
            Script = $ScriptPath
            Error = "No successful script executions"
        }
    }
    
    # Analysis
    $sortedTimings = $timings | Sort-Object
    $mean = ($timings | Measure-Object -Average).Average
    
    return @{
        Script = $ScriptPath
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Iterations = $Iterations
        ErrorCount = $errorCount
        
        # Timing metrics (milliseconds for scripts)
        MeanMilliseconds = $mean
        MedianMilliseconds = $sortedTimings[[math]::Floor($sortedTimings.Count / 2)]
        P95Milliseconds = $sortedTimings[[math]::Floor(0.95 * $sortedTimings.Count)]
        MinMilliseconds = $sortedTimings[0]
        MaxMilliseconds = $sortedTimings[-1]
        
        # Classification
        PerformanceClass = Get-ScriptPerformanceClass $mean
    }
}

function Get-ScriptPerformanceClass {
    param([double]$MeanTimeMilliseconds)
    
    if ($MeanTimeMilliseconds -lt 100) { return "fast" }
    elseif ($MeanTimeMilliseconds -lt 1000) { return "acceptable" }
    elseif ($MeanTimeMilliseconds -lt 5000) { return "slow" }
    else { return "very_slow" }
}

function Compare-PowerShellImplementations {
    <#
    .SYNOPSIS
        Compare multiple PowerShell implementations
    #>
    param(
        [hashtable]$Implementations,  # Name -> ScriptBlock
        [hashtable]$TestData = @{},
        [int]$Iterations = 1000
    )
    
    Write-Host "Comparing $($Implementations.Count) implementations..." -ForegroundColor Cyan
    
    $results = @{}
    
    # Benchmark each implementation
    foreach ($name in $Implementations.Keys) {
        Write-Host "  Testing: $name" -ForegroundColor Yellow
        $results[$name] = Measure-FunctionPerformance -Function $Implementations[$name] -Parameters $TestData -Iterations $Iterations -FunctionName $name
    }
    
    # Calculate relative performance
    $validResults = $results.GetEnumerator() | Where-Object { -not $_.Value.ContainsKey('Error') }
    
    if ($validResults.Count -gt 0) {
        $fastest = $validResults | Sort-Object { $_.Value.MeanMicroseconds } | Select-Object -First 1
        $fastestTime = $fastest.Value.MeanMicroseconds
        
        foreach ($entry in $validResults) {
            $entry.Value.RelativeSpeed = $entry.Value.MeanMicroseconds / $fastestTime
            $entry.Value.SpeedupFactor = $fastestTime / $entry.Value.MeanMicroseconds
            $entry.Value.IsFastest = ($entry.Key -eq $fastest.Key)
        }
    }
    
    return @{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Implementations = $results
        Summary = Get-ComparisonSummary $results
    }
}

function Get-ComparisonSummary {
    param([hashtable]$Results)
    
    $validResults = $Results.GetEnumerator() | Where-Object { -not $_.Value.ContainsKey('Error') }
    
    if ($validResults.Count -eq 0) {
        return @{ Error = "No valid results to compare" }
    }
    
    $times = $validResults | ForEach-Object { $_.Value.MeanMicroseconds }
    $fastest = $validResults | Sort-Object { $_.Value.MeanMicroseconds } | Select-Object -First 1
    $slowest = $validResults | Sort-Object { $_.Value.MeanMicroseconds } | Select-Object -Last 1
    
    return @{
        ImplementationsTested = $validResults.Count
        FastestImplementation = $fastest.Key
        SlowestImplementation = $slowest.Key
        SpeedRatio = $slowest.Value.MeanMicroseconds / $fastest.Value.MeanMicroseconds
        AveragePerformanceMicroseconds = ($times | Measure-Object -Average).Average
        PerformanceSpreadMicroseconds = ($times | Measure-Object -Maximum).Maximum - ($times | Measure-Object -Minimum).Minimum
    }
}

function Test-PerformanceRegression {
    <#
    .SYNOPSIS
        Test for performance regressions against baseline
    #>
    param(
        [string]$BaselineFile = "$OutputDir/powershell_baseline.json",
        [double]$TolerancePercent = 10.0
    )
    
    Write-Host "🔍 Running PowerShell performance regression test..." -ForegroundColor Cyan
    
    # Define core test suite
    $testSuite = Get-CoreTestSuite
    
    # Run current benchmarks
    $currentResults = @{}
    foreach ($testName in $testSuite.Keys) {
        Write-Host "  Testing: $testName" -ForegroundColor Yellow
        $currentResults[$testName] = Measure-FunctionPerformance -Function $testSuite[$testName] -FunctionName $testName -Iterations $Iterations
    }
    
    # Load baseline
    $baseline = @{}
    if (Test-Path $BaselineFile) {
        try {
            $baseline = Get-Content $BaselineFile | ConvertFrom-Json -AsHashtable
            Write-Host "✅ Loaded baseline from: $BaselineFile" -ForegroundColor Green
        }
        catch {
            Write-Warning "Failed to load baseline: $($_.Exception.Message)"
        }
    }
    else {
        Write-Host "⚠️  No baseline found, creating new baseline..." -ForegroundColor Yellow
    }
    
    # Analyze regressions
    $regressionAnalysis = Compare-WithBaseline -Current $currentResults -Baseline $baseline -TolerancePercent $TolerancePercent
    
    # Save new baseline if no regressions
    if ($regressionAnalysis.Passed -and $baseline.Count -gt 0) {
        Save-Baseline -Results $currentResults -BaselineFile $BaselineFile
    }
    elseif ($baseline.Count -eq 0) {
        # First run - establish baseline
        Save-Baseline -Results $currentResults -BaselineFile $BaselineFile
        Write-Host "📊 Baseline established: $BaselineFile" -ForegroundColor Green
    }
    
    # Generate comprehensive report
    $regressionReport = @{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        CurrentResults = $currentResults
        BaselineFile = $BaselineFile
        RegressionAnalysis = $regressionAnalysis
        TolerancePercent = $TolerancePercent
        SystemInfo = Get-SystemInfo
    }
    
    # Save regression test results
    $reportFile = "$OutputDir/regression_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $regressionReport | ConvertTo-Json -Depth 10 | Out-File $reportFile -Encoding UTF8
    
    Write-Host "`n📊 Regression test results saved to: $reportFile" -ForegroundColor Green
    
    return $regressionReport
}

function Compare-WithBaseline {
    param(
        [hashtable]$Current,
        [hashtable]$Baseline,
        [double]$TolerancePercent
    )
    
    $regressions = @()
    $improvements = @()
    $toleranceFactor = 1 + ($TolerancePercent / 100)
    
    foreach ($testName in $Current.Keys) {
        $currentMetrics = $Current[$testName]
        
        if ($currentMetrics.ContainsKey('Error')) {
            continue
        }
        
        if (-not $Baseline.ContainsKey($testName)) {
            continue
        }
        
        $baselineMetrics = $Baseline[$testName]
        
        # Check timing regression
        $currentTime = $currentMetrics.MeanMicroseconds
        $baselineTime = $baselineMetrics.MeanMicroseconds
        
        if ($currentTime -gt ($baselineTime * $toleranceFactor)) {
            $degradationPct = (($currentTime - $baselineTime) / $baselineTime) * 100
            $regressions += @{
                Test = $testName
                Metric = "timing"
                BaselineMicroseconds = $baselineTime
                CurrentMicroseconds = $currentTime
                DegradationPercent = $degradationPct
            }
        }
        elseif ($currentTime -lt ($baselineTime * 0.9)) {  # 10% improvement threshold
            $improvementPct = (($baselineTime - $currentTime) / $baselineTime) * 100
            $improvements += @{
                Test = $testName
                Metric = "timing"
                BaselineMicroseconds = $baselineTime
                CurrentMicroseconds = $currentTime
                ImprovementPercent = $improvementPct
            }
        }
        
        # Check memory regression
        $currentMemory = $currentMetrics.MemoryDeltaMB
        $baselineMemory = $baselineMetrics.MemoryDeltaMB
        
        if ($baselineMemory -gt 0 -and $currentMemory -gt ($baselineMemory * $toleranceFactor)) {
            $memoryDegradation = (($currentMemory - $baselineMemory) / $baselineMemory) * 100
            $regressions += @{
                Test = $testName
                Metric = "memory"
                BaselineMB = $baselineMemory
                CurrentMB = $currentMemory
                DegradationPercent = $memoryDegradation
            }
        }
    }
    
    return @{
        Passed = ($regressions.Count -eq 0)
        Regressions = $regressions
        Improvements = $improvements
        TotalTests = $Current.Count
        BaselineTests = $Baseline.Count
    }
}

function Save-Baseline {
    param(
        [hashtable]$Results,
        [string]$BaselineFile
    )
    
    # Extract baseline metrics
    $baselineData = @{}
    foreach ($testName in $Results.Keys) {
        $metrics = $Results[$testName]
        if (-not $metrics.ContainsKey('Error')) {
            $baselineData[$testName] = @{
                MeanMicroseconds = $metrics.MeanMicroseconds
                P95Microseconds = $metrics.P95Microseconds
                OperationsPerSecond = $metrics.OperationsPerSecond
                MemoryDeltaMB = $metrics.MemoryDeltaMB
            }
        }
    }
    
    $baselineData | ConvertTo-Json -Depth 5 | Out-File $BaselineFile -Encoding UTF8
    Write-Verbose "Baseline saved to: $BaselineFile"
}

function Get-CoreTestSuite {
    <#
    .SYNOPSIS
        Define core test suite for regression testing
    #>
    
    return @{
        "file_filtering" = {
            # Test file filtering performance (based on secret-audit.ps1)
            $testFiles = 1..1000 | ForEach-Object { "test_file_$_.txt" }
            $binaryExtensions = @('.exe', '.dll', '.bin', '.jpg', '.png')
            
            $filtered = $testFiles | Where-Object {
                $extension = [System.IO.Path]::GetExtension($_).ToLower()
                $extension -notin $binaryExtensions
            }
            
            return $filtered.Count
        }
        
        "regex_compilation" = {
            # Test regex compilation performance
            $patterns = @(
                'ghp_[a-zA-Z0-9]{36}',
                'AKIA[0-9A-Z]{16}',
                'sk-[a-zA-Z0-9]{48}',
                'eyJ[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+'
            )
            
            $compiled = foreach ($pattern in $patterns) {
                [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::Compiled)
            }
            
            return $compiled.Count
        }
        
        "string_processing" = {
            # Test string processing performance
            $testString = "This is a test string with some content to process " * 100
            $processed = $testString -replace "test", "sample" -replace "content", "data"
            return $processed.Length
        }
        
        "array_operations" = {
            # Test array operations
            $array = 1..1000
            $filtered = $array | Where-Object { $_ % 2 -eq 0 }
            $mapped = $filtered | ForEach-Object { $_ * 2 }
            return $mapped.Count
        }
        
        "hashtable_operations" = {
            # Test hashtable performance
            $hash = @{}
            for ($i = 0; $i -lt 1000; $i++) {
                $hash["key_$i"] = "value_$i"
            }
            
            $lookups = 0
            for ($i = 0; $i -lt 100; $i++) {
                if ($hash.ContainsKey("key_$i")) {
                    $lookups++
                }
            }
            
            return $lookups
        }
    }
}

function Measure-MemoryPressure {
    <#
    .SYNOPSIS
        Analyze memory usage patterns and pressure
    #>
    param(
        [scriptblock]$Operation,
        [hashtable]$Parameters = @{},
        [int]$MonitoringIntervalMS = 100
    )
    
    Write-Host "📊 Starting memory pressure analysis..." -ForegroundColor Cyan
    
    # Background memory monitoring
    $memoryJob = Start-Job -ScriptBlock {
        param($IntervalMS, $Operation, $Parameters)
        
        $measurements = @()
        $process = Get-Process -Id $using:PID
        
        while ($true) {
            try {
                $process.Refresh()
                $measurements += @{
                    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
                    WorkingSetMB = [math]::Round($process.WorkingSet64 / 1MB, 2)
                    PrivateMemoryMB = [math]::Round($process.PrivateMemorySize64 / 1MB, 2)
                }
                
                Start-Sleep -Milliseconds $IntervalMS
            }
            catch {
                break
            }
        }
        
        return $measurements
    } -ArgumentList $MonitoringIntervalMS, $Operation, $Parameters
    
    # Execute operation
    [System.GC]::Collect()
    $startMemory = [System.GC]::GetTotalMemory($false)
    $startTime = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $result = & $Operation @Parameters
    }
    finally {
        $startTime.Stop()
        [System.GC]::Collect()
        $endMemory = [System.GC]::GetTotalMemory($false)
        
        # Stop monitoring
        Stop-Job $memoryJob
        $memoryMeasurements = Receive-Job $memoryJob
        Remove-Job $memoryJob
    }
    
    # Analyze memory usage
    if ($memoryMeasurements -and $memoryMeasurements.Count -gt 0) {
        $workingSetValues = $memoryMeasurements | ForEach-Object { $_.WorkingSetMB }
        $peakMemory = ($workingSetValues | Measure-Object -Maximum).Maximum
        $avgMemory = ($workingSetValues | Measure-Object -Average).Average
        $memoryGrowth = $peakMemory - $workingSetValues[0]
    }
    else {
        $peakMemory = 0
        $avgMemory = 0
        $memoryGrowth = 0
    }
    
    return @{
        ExecutionTimeMS = $startTime.Elapsed.TotalMilliseconds
        ManagedMemoryDeltaMB = ($endMemory - $startMemory) / 1MB
        PeakWorkingSetMB = $peakMemory
        AverageWorkingSetMB = $avgMemory
        MemoryGrowthMB = $memoryGrowth
        MemoryEfficiencyScore = Get-MemoryEfficiencyScore $peakMemory $startTime.Elapsed.TotalMilliseconds
        DetailedMeasurements = $memoryMeasurements
    }
}

function Get-MemoryEfficiencyScore {
    param(
        [double]$PeakMemoryMB,
        [double]$ExecutionTimeMS
    )
    
    # Simple efficiency scoring: lower memory + faster execution = higher score
    $memoryScore = [math]::Max(0, 100 - ($PeakMemoryMB / 5))    # 500MB = 0 points
    $timeScore = [math]::Max(0, 100 - ($ExecutionTimeMS / 100)) # 10s = 0 points
    
    return [math]::Round(($memoryScore + $timeScore) / 2, 1)
}

function Get-SystemInfo {
    <#
    .SYNOPSIS
        Get system information for benchmark context
    #>
    
    $info = @{
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        Platform = $PSVersionTable.Platform
        OS = $PSVersionTable.OS
        ProcessorCount = $env:NUMBER_OF_PROCESSORS
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    # Get memory information
    try {
        $computerInfo = Get-ComputerInfo -Property TotalPhysicalMemory, AvailableMemory -ErrorAction SilentlyContinue
        if ($computerInfo) {
            $info.TotalMemoryGB = [math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 1)
            $info.AvailableMemoryGB = [math]::Round($computerInfo.AvailableMemory / 1GB, 1)
        }
    }
    catch {
        Write-Verbose "Could not retrieve detailed system memory information"
    }
    
    return $info
}

function Export-PerformanceReport {
    <#
    .SYNOPSIS
        Export comprehensive performance report
    #>
    param(
        [hashtable]$Results,
        [string]$ReportType = "comprehensive",
        [string]$OutputFile
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Generate report based on type
    switch ($ReportType) {
        "comprehensive" {
            $report = @{
                ReportType = "PowerShell Performance Analysis"
                Timestamp = $timestamp
                SystemInfo = Get-SystemInfo
                Results = $Results
                Summary = Get-ResultsSummary $Results
                Recommendations = Get-PerformanceRecommendations $Results
            }
        }
        "comparison" {
            $report = @{
                ReportType = "Implementation Comparison"
                Timestamp = $timestamp
                Comparison = $Results
                Winner = $Results.Summary.FastestImplementation
                Analysis = Get-ComparisonAnalysis $Results
            }
        }
        "regression" {
            $report = @{
                ReportType = "Performance Regression Test"
                Timestamp = $timestamp
                RegressionResults = $Results
                Status = if ($Results.RegressionAnalysis.Passed) { "PASSED" } else { "FAILED" }
                Summary = Get-RegressionSummary $Results
            }
        }
    }
    
    # Save report
    if (-not $OutputFile) {
        $OutputFile = "$OutputDir/powershell_${ReportType}_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File $OutputFile -Encoding UTF8
    Write-Host "📊 Report exported to: $OutputFile" -ForegroundColor Green
    
    return $report
}

function Get-ResultsSummary {
    param([hashtable]$Results)
    
    $validResults = @()
    $errorCount = 0
    
    foreach ($key in $Results.Keys) {
        if ($Results[$key].ContainsKey('Error')) {
            $errorCount++
        }
        else {
            $validResults += $Results[$key]
        }
    }
    
    if ($validResults.Count -eq 0) {
        return @{ Error = "No valid results to summarize" }
    }
    
    $times = $validResults | ForEach-Object { $_.MeanMicroseconds }
    $opsPerSec = $validResults | ForEach-Object { $_.OperationsPerSecond }
    
    return @{
        TotalTests = $Results.Count
        SuccessfulTests = $validResults.Count
        FailedTests = $errorCount
        FastestTestMicroseconds = ($times | Measure-Object -Minimum).Minimum
        SlowestTestMicroseconds = ($times | Measure-Object -Maximum).Maximum
        AveragePerformanceMicroseconds = ($times | Measure-Object -Average).Average
        TotalThroughputOpsPerSec = ($opsPerSec | Measure-Object -Sum).Sum
        PerformanceSpreadRatio = if ($times.Count -gt 0) { 
            ($times | Measure-Object -Maximum).Maximum / ($times | Measure-Object -Minimum).Minimum 
        } else { 0 }
    }
}

function Get-PerformanceRecommendations {
    param([hashtable]$Results)
    
    $recommendations = @()
    $validResults = $Results.GetEnumerator() | Where-Object { -not $_.Value.ContainsKey('Error') }
    
    foreach ($entry in $validResults) {
        $name = $entry.Key
        $metrics = $entry.Value
        
        # Analyze performance characteristics
        if ($metrics.PerformanceClass -eq "slow" -or $metrics.PerformanceClass -eq "very_slow") {
            $recommendations += "⚠️ $name is slow ($($metrics.MeanMicroseconds.ToString('F2'))μs) - consider optimization"
        }
        
        if ($metrics.CoefficientOfVariation -gt 0.2) {
            $recommendations += "📊 $name has high variability (CV: $($metrics.CoefficientOfVariation.ToString('F3'))) - investigate consistency"
        }
        
        if ($metrics.MemoryDeltaMB -gt 10) {
            $recommendations += "💾 $name uses significant memory ($($metrics.MemoryDeltaMB.ToString('F2'))MB) - consider memory optimization"
        }
        
        if ($metrics.OperationsPerSecond -lt 1000) {
            $recommendations += "⚡ $name has low throughput ($($metrics.OperationsPerSecond) ops/sec) - consider algorithmic improvements"
        }
    }
    
    if ($recommendations.Count -eq 0) {
        $recommendations += "✅ All functions performing within acceptable parameters"
    }
    
    return $recommendations
}

# Main execution logic
function Invoke-PerformanceAnalysis {
    Write-Host "🚀 PowerShell Performance Analyzer for Strataregula" -ForegroundColor Cyan
    Write-Host "Configuration: Iterations=$Iterations, Warmup=$WarmupIterations" -ForegroundColor Yellow
    Write-Host "Output Directory: $outputPath" -ForegroundColor Yellow
    Write-Host ""
    
    if ($RegressionTest) {
        # Run regression testing
        $results = Test-PerformanceRegression -TolerancePercent 10.0
        Export-PerformanceReport -Results $results -ReportType "regression"
        
        # Display results
        Write-Host "`n" + "="*60 -ForegroundColor Cyan
        Write-Host "REGRESSION TEST RESULTS" -ForegroundColor Cyan
        Write-Host "="*60 -ForegroundColor Cyan
        
        $analysis = $results.RegressionAnalysis
        if ($analysis.Passed) {
            Write-Host "✅ PASSED: No performance regressions detected" -ForegroundColor Green
        }
        else {
            Write-Host "❌ FAILED: Performance regressions detected" -ForegroundColor Red
        }
        
        Write-Host "Tests run: $($analysis.TotalTests)" -ForegroundColor White
        
        if ($analysis.Regressions.Count -gt 0) {
            Write-Host "`n🚨 Regressions:" -ForegroundColor Red
            foreach ($reg in $analysis.Regressions) {
                Write-Host "  $($reg.Test) ($($reg.Metric)): $($reg.DegradationPercent.ToString('F1'))% slower" -ForegroundColor Red
            }
        }
        
        if ($analysis.Improvements.Count -gt 0) {
            Write-Host "`n🚀 Improvements:" -ForegroundColor Green
            foreach ($imp in $analysis.Improvements) {
                Write-Host "  $($imp.Test) ($($imp.Metric)): $($imp.ImprovementPercent.ToString('F1'))% faster" -ForegroundColor Green
            }
        }
        
        # Exit with appropriate code
        exit (if ($analysis.Passed) { 0 } else { 1 })
    }
    elseif ($ScriptPath) {
        # Benchmark specific script
        $results = Measure-ScriptPerformance -ScriptPath $ScriptPath -Iterations $Iterations
        Export-PerformanceReport -Results $results -ReportType "script" -OutputFile "$OutputDir/script_$(Split-Path $ScriptPath -LeafBase)_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        
        Write-Host "`nScript Performance Results:" -ForegroundColor Cyan
        Write-Host "Script: $($results.Script)" -ForegroundColor White
        Write-Host "Mean execution time: $($results.MeanMilliseconds.ToString('F2'))ms" -ForegroundColor White
        Write-Host "Performance class: $($results.PerformanceClass)" -ForegroundColor White
    }
    elseif ($Compare) {
        # Run implementation comparisons
        Write-Host "⚖️ Running implementation comparisons..." -ForegroundColor Cyan
        
        # Example comparison: Different file filtering approaches
        $implementations = @{
            "pipeline_filter" = {
                $files = 1..1000 | ForEach-Object { "file_$_.txt" }
                return ($files | Where-Object { $_ -like "*.txt" }).Count
            }
            
            "foreach_filter" = {
                $files = 1..1000 | ForEach-Object { "file_$_.txt" }
                $filtered = @()
                foreach ($file in $files) {
                    if ($file -like "*.txt") {
                        $filtered += $file
                    }
                }
                return $filtered.Count
            }
            
            "dotnet_filter" = {
                $files = 1..1000 | ForEach-Object { "file_$_.txt" }
                $filtered = [System.Collections.Generic.List[string]]::new()
                foreach ($file in $files) {
                    if ($file.EndsWith('.txt')) {
                        $filtered.Add($file)
                    }
                }
                return $filtered.Count
            }
        }
        
        $results = Compare-PowerShellImplementations -Implementations $implementations -Iterations $Iterations
        Export-PerformanceReport -Results $results -ReportType "comparison"
        
        # Display comparison results
        Write-Host "`n⚖️ Implementation Comparison Results:" -ForegroundColor Cyan
        Write-Host "Winner: $($results.Summary.FastestImplementation)" -ForegroundColor Green
        Write-Host "Speed ratio: $($results.Summary.SpeedRatio.ToString('F1'))x" -ForegroundColor White
        
        Write-Host "`nDetailed Results:" -ForegroundColor Yellow
        foreach ($name in $results.Implementations.Keys) {
            $metrics = $results.Implementations[$name]
            if (-not $metrics.ContainsKey('Error')) {
                $status = if ($metrics.IsFastest) { "🏆" } elseif ($metrics.RelativeSpeed -lt 2) { "✅" } else { "⚠️" }
                Write-Host "  $name`: $($metrics.MeanMicroseconds.ToString('F2'))μs ($(($metrics.RelativeSpeed).ToString('F1'))x) $status" -ForegroundColor White
            }
            else {
                Write-Host "  $name`: ERROR - $($metrics.Error)" -ForegroundColor Red
            }
        }
    }
    elseif ($MemoryAnalysis) {
        # Run memory analysis
        Write-Host "💾 Running memory analysis..." -ForegroundColor Cyan
        
        $testOperation = {
            # Simulate memory-intensive operation
            $largeArray = 1..10000 | ForEach-Object { "Item_$_" }
            $processed = $largeArray | Where-Object { $_.Length -gt 5 }
            return $processed.Count
        }
        
        $memoryResults = Measure-MemoryPressure -Operation $testOperation
        
        Write-Host "`n💾 Memory Analysis Results:" -ForegroundColor Cyan
        Write-Host "Execution time: $($memoryResults.ExecutionTimeMS.ToString('F2'))ms" -ForegroundColor White
        Write-Host "Peak working set: $($memoryResults.PeakWorkingSetMB.ToString('F2'))MB" -ForegroundColor White
        Write-Host "Memory growth: $($memoryResults.MemoryGrowthMB.ToString('F2'))MB" -ForegroundColor White
        Write-Host "Efficiency score: $($memoryResults.MemoryEfficiencyScore)/100" -ForegroundColor White
    }
    else {
        # Default comprehensive analysis
        Write-Host "🔧 Running comprehensive PowerShell performance analysis..." -ForegroundColor Cyan
        
        $testSuite = Get-CoreTestSuite
        $results = @{}
        
        foreach ($testName in $testSuite.Keys) {
            Write-Host "  Testing: $testName" -ForegroundColor Yellow
            $results[$testName] = Measure-FunctionPerformance -Function $testSuite[$testName] -FunctionName $testName -Iterations $Iterations
        }
        
        $report = Export-PerformanceReport -Results $results -ReportType "comprehensive"
        
        # Display summary
        Write-Host "`n" + "="*60 -ForegroundColor Cyan
        Write-Host "POWERSHELL PERFORMANCE ANALYSIS SUMMARY" -ForegroundColor Cyan
        Write-Host "="*60 -ForegroundColor Cyan
        
        $summary = $report.Summary
        Write-Host "Total tests: $($summary.TotalTests)" -ForegroundColor White
        Write-Host "Successful: $($summary.SuccessfulTests)" -ForegroundColor Green
        Write-Host "Failed: $($summary.FailedTests)" -ForegroundColor Red
        Write-Host "Fastest test: $($summary.FastestTestMicroseconds.ToString('F2'))μs" -ForegroundColor Green
        Write-Host "Slowest test: $($summary.SlowestTestMicroseconds.ToString('F2'))μs" -ForegroundColor Yellow
        Write-Host "Performance spread: $($summary.PerformanceSpreadRatio.ToString('F1'))x" -ForegroundColor White
        
        if ($report.Recommendations.Count -gt 0) {
            Write-Host "`n💡 Recommendations:" -ForegroundColor Yellow
            foreach ($rec in $report.Recommendations) {
                Write-Host "  $rec" -ForegroundColor White
            }
        }
    }
    
    Write-Host "`n✅ PowerShell performance analysis complete!" -ForegroundColor Green
}

# Execute main analysis
Invoke-PerformanceAnalysis
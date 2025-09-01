# PowerShell Performance Best Practices

## Overview
PowerShell-specific optimization techniques for file processing, pattern matching, and system operations.

## Core Optimization Patterns

### 1. Pipeline Optimization

```powershell
# ❌ Slow: Creating unnecessary arrays
$results = @()
Get-ChildItem | ForEach-Object { $results += $_.Name }

# ✅ Fast: Direct pipeline processing
$results = Get-ChildItem | ForEach-Object { $_.Name }

# ✅ Fastest: One-liner with optimized cmdlets
$results = (Get-ChildItem).Name
```

### 2. String Operations

```powershell
# ❌ Slow: String concatenation in loops
$output = ""
foreach ($item in $items) {
    $output += "$item`n"  # Creates new string each time
}

# ✅ Fast: StringBuilder for large concatenations
$sb = [System.Text.StringBuilder]::new()
foreach ($item in $items) {
    [void]$sb.AppendLine($item)
}
$output = $sb.ToString()

# ✅ Fastest: Join operation
$output = $items -join "`n"
```

### 3. Regular Expression Optimization

```powershell
# ❌ Slow: Recompiling regex in loops
foreach ($line in $content) {
    if ($line -match 'pattern') { ... }  # Recompiles each time
}

# ✅ Fast: Pre-compiled regex
$regex = [regex]::new('pattern', [System.Text.RegularExpressions.RegexOptions]::Compiled)
foreach ($line in $content) {
    if ($regex.IsMatch($line)) { ... }
}

# ✅ Optimized: Batch processing with Select-String
$matches = $content | Select-String -Pattern 'pattern'
```

### 4. File Operations

```powershell
# ❌ Slow: Reading files individually
$allContent = @()
foreach ($file in $files) {
    $allContent += Get-Content $file
}

# ✅ Fast: Batch file reading
$allContent = $files | ForEach-Object { Get-Content $_ }

# ✅ Optimized: Raw content for large files
$allContent = $files | ForEach-Object { 
    [System.IO.File]::ReadAllText($_.FullName) 
}
```

## Memory Management

### 1. Avoiding Memory Bloat

```powershell
# ❌ Memory inefficient: Loading everything into memory
$allFiles = Get-ChildItem -Recurse
$results = $allFiles | Where-Object { $_.Length -gt 1MB }

# ✅ Memory efficient: Streaming processing
$results = Get-ChildItem -Recurse | Where-Object { $_.Length -gt 1MB }
```

### 2. Garbage Collection

```powershell
# ✅ Explicit cleanup for large operations
$largeArray = @(1..1000000)
# ... process data ...
$largeArray = $null
[System.GC]::Collect()  # Force cleanup when needed
```

### 3. Variable Scoping

```powershell
# ❌ Global scope pollution
$global:cache = @{}

# ✅ Appropriate scoping
function Process-Data {
    [CmdletBinding()]
    param()
    
    $local:cache = @{}  # Function-scoped
    # ... processing ...
}
```

## Specific Optimizations for Secret Scanning

Based on the `secret-audit.ps1` analysis:

### 1. File Filtering Optimization

```powershell
# ✅ Optimized file filtering (from secret-audit.ps1)
function Should-ExcludeFile {
    param($FilePath)
    
    # Size check first (fastest)
    try {
        $fileInfo = Get-Item $FilePath -ErrorAction SilentlyContinue
        if ($fileInfo -and $fileInfo.Length -gt 2MB) {
            return $true
        }
    } catch {
        return $true
    }
    
    # Extension check (pre-computed hash set)
    $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
    if ($extension -in $script:binaryExtensions) {
        return $true
    }
    
    # Pattern matching last (most expensive)
    foreach ($pattern in $excludePatterns) {
        if ($FilePath -like "*$pattern*") {
            return $true
        }
    }
    return $false
}
```

### 2. Regex Performance

```powershell
# ✅ Pre-compiled regex for pattern matching
$script:compiledPatterns = @()
foreach ($pattern in $secretPatterns) {
    $script:compiledPatterns += [regex]::new(
        $pattern.Pattern, 
        [System.Text.RegularExpressions.RegexOptions]::Compiled -bor
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
}

# Use in scanning loop
foreach ($compiledPattern in $script:compiledPatterns) {
    $matches = $compiledPattern.Matches($content)
    # Process matches...
}
```

### 3. Batch File Processing

```powershell
# ✅ Optimized batch file processing
$files = Get-ChildItem -Path $ScanPath -Recurse -File | 
         Where-Object { -not (Should-ExcludeFile $_.FullName) }

# Process in chunks to manage memory
$chunkSize = 100
for ($i = 0; $i -lt $files.Count; $i += $chunkSize) {
    $chunk = $files[$i..($i + $chunkSize - 1)]
    $chunk | ForEach-Object -Parallel {
        # Parallel processing for I/O bound operations
        Process-FileForSecrets $_
    } -ThrottleLimit 10
}
```

## Performance Measurement

### 1. Accurate Timing

```powershell
function Measure-Performance {
    param(
        [scriptblock]$ScriptBlock,
        [int]$Iterations = 1000,
        [int]$WarmupIterations = 100
    )
    
    # Warmup
    for ($i = 0; $i -lt $WarmupIterations; $i++) {
        & $ScriptBlock | Out-Null
    }
    
    # Measure
    $times = @()
    for ($i = 0; $i -lt $Iterations; $i++) {
        $start = [System.Diagnostics.Stopwatch]::StartNew()
        & $ScriptBlock | Out-Null
        $start.Stop()
        $times += $start.Elapsed.TotalMicroseconds
    }
    
    return @{
        Mean = ($times | Measure-Object -Average).Average
        P95 = ($times | Sort-Object)[[math]::Floor(0.95 * $times.Count)]
        Min = ($times | Measure-Object -Minimum).Minimum
        Max = ($times | Measure-Object -Maximum).Maximum
    }
}
```

### 2. Memory Tracking

```powershell
function Measure-MemoryUsage {
    param([scriptblock]$ScriptBlock)
    
    [System.GC]::Collect()
    $before = [System.GC]::GetTotalMemory($false)
    
    $result = & $ScriptBlock
    
    [System.GC]::Collect()
    $after = [System.GC]::GetTotalMemory($false)
    
    return @{
        Result = $result
        MemoryDelta = $after - $before
        MemoryDeltaMB = ($after - $before) / 1MB
    }
}
```

## Common PowerShell Bottlenecks

### 1. Array Operations
```powershell
# ❌ Slow: Array concatenation
$results = @()
foreach ($item in $largeArray) {
    $results += $item  # O(n) operation each time
}

# ✅ Fast: ArrayList or List
$results = [System.Collections.ArrayList]::new()
foreach ($item in $largeArray) {
    [void]$results.Add($item)  # O(1) operation
}
```

### 2. Pipeline Efficiency
```powershell
# ❌ Inefficient: Multiple pipeline passes
$filtered = $data | Where-Object { $_.Status -eq 'Active' }
$processed = $filtered | ForEach-Object { Process-Item $_ }
$sorted = $processed | Sort-Object Name

# ✅ Efficient: Single pipeline
$results = $data | 
    Where-Object { $_.Status -eq 'Active' } |
    ForEach-Object { Process-Item $_ } |
    Sort-Object Name
```

### 3. Object Creation
```powershell
# ❌ Expensive: PSCustomObject in tight loops
$results = foreach ($item in $items) {
    [PSCustomObject]@{
        Name = $item.Name
        Value = $item.Value
    }
}

# ✅ Cheaper: Hashtables for simple data
$results = foreach ($item in $items) {
    @{
        Name = $item.Name
        Value = $item.Value
    }
}
```

## PowerShell-Specific Optimizations

### 1. Parameter Binding
```powershell
# ✅ Strongly typed parameters for better performance
function Process-Data {
    [CmdletBinding()]
    param(
        [string[]]$InputData,
        [int]$ChunkSize = 100,
        [ValidateSet('Fast', 'Thorough')]
        [string]$Mode = 'Fast'
    )
    # Processing logic...
}
```

### 2. Error Handling
```powershell
# ❌ Slow: Try-catch for expected conditions
try {
    $value = $hash[$key]
} catch {
    $value = $default
}

# ✅ Fast: Conditional testing
$value = if ($hash.ContainsKey($key)) { $hash[$key] } else { $default }
```

### 3. Output Optimization
```powershell
# ❌ Slow: Write-Host in performance-critical code
foreach ($item in $largeCollection) {
    Write-Host "Processing $item"  # Expensive I/O
    Process-Item $item
}

# ✅ Fast: Conditional verbose output
foreach ($item in $largeCollection) {
    if ($VerbosePreference -eq 'Continue') {
        Write-Verbose "Processing $item"
    }
    Process-Item $item
}
```

## Benchmarking PowerShell Code

### 1. Function Benchmarking
```powershell
# Benchmark framework for PowerShell functions
function Benchmark-Function {
    param(
        [scriptblock]$Function,
        [hashtable]$Parameters = @{},
        [int]$Iterations = 1000
    )
    
    $measurements = @()
    
    # Warmup
    for ($i = 0; $i -lt 100; $i++) {
        & $Function @Parameters | Out-Null
    }
    
    # Benchmark
    for ($i = 0; $i -lt $Iterations; $i++) {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        & $Function @Parameters | Out-Null
        $stopwatch.Stop()
        $measurements += $stopwatch.Elapsed.TotalMicroseconds
    }
    
    $sorted = $measurements | Sort-Object
    return @{
        MeanMicroseconds = ($measurements | Measure-Object -Average).Average
        P95Microseconds = $sorted[[math]::Floor(0.95 * $sorted.Count)]
        MinMicroseconds = $sorted[0]
        MaxMicroseconds = $sorted[-1]
        TotalIterations = $Iterations
    }
}
```

### 2. Comparative Benchmarking
```powershell
function Compare-Implementations {
    param(
        [hashtable]$Implementations,
        [hashtable]$TestData,
        [int]$Iterations = 1000
    )
    
    $results = @{}
    
    foreach ($name in $Implementations.Keys) {
        Write-Host "Benchmarking: $name"
        $results[$name] = Benchmark-Function -Function $Implementations[$name] -Parameters $TestData -Iterations $Iterations
    }
    
    # Generate comparison report
    $fastest = ($results.GetEnumerator() | Sort-Object { $_.Value.MeanMicroseconds })[0]
    
    Write-Host "`nPerformance Comparison:"
    Write-Host "Name".PadRight(20) + "Mean (μs)".PadRight(12) + "P95 (μs)".PadRight(12) + "Relative"
    Write-Host ("-" * 60)
    
    foreach ($entry in $results.GetEnumerator() | Sort-Object { $_.Value.MeanMicroseconds }) {
        $ratio = $entry.Value.MeanMicroseconds / $fastest.Value.MeanMicroseconds
        Write-Host ($entry.Key.PadRight(20) + 
                   "{0:F2}" -f $entry.Value.MeanMicroseconds).PadRight(12) + 
                   ("{0:F2}" -f $entry.Value.P95Microseconds).PadRight(12) + 
                   "{0:F1}x" -f $ratio
    }
}
```

## Real-World Example: File Processing Optimization

Based on the secret scanning script optimization:

```powershell
# ✅ Optimized file processing pipeline
function Invoke-OptimizedScan {
    param(
        [string]$ScanPath,
        [string[]]$Patterns,
        [string[]]$ExcludePatterns
    )
    
    # Pre-compile all regex patterns
    $compiledPatterns = foreach ($pattern in $Patterns) {
        [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::Compiled)
    }
    
    # Get files with efficient filtering
    $files = Get-ChildItem -Path $ScanPath -Recurse -File |
        Where-Object { 
            $_.Length -le 2MB -and
            $_.Extension -notin $script:binaryExtensions -and
            -not ($ExcludePatterns | Where-Object { $_.FullName -like "*$_*" })
        }
    
    # Process files in parallel chunks
    $files | ForEach-Object -Parallel {
        $compiledPatterns = $using:compiledPatterns
        $content = [System.IO.File]::ReadAllText($_.FullName)
        
        foreach ($regex in $compiledPatterns) {
            $matches = $regex.Matches($content)
            if ($matches.Count -gt 0) {
                # Return match information
                foreach ($match in $matches) {
                    @{
                        File = $_.FullName
                        Pattern = $regex.ToString()
                        Match = $match.Value
                        Index = $match.Index
                    }
                }
            }
        }
    } -ThrottleLimit 10
}
```

## Performance Anti-Patterns

### 1. PowerShell-Specific Pitfalls

```powershell
# ❌ Array concatenation in loops
$results = @()
foreach ($item in $items) {
    $results += $item  # O(n) complexity - recreates array
}

# ❌ Unnecessary object wrapping
$data | ForEach-Object { [PSCustomObject]@{ Value = $_ } }

# ❌ String interpolation in hot paths
foreach ($item in $largeCollection) {
    Write-Output "Processing: $($item.Name) at $(Get-Date)"
}

# ❌ Nested pipeline calls
$data | ForEach-Object { 
    $_ | Where-Object { $_.Active } | ForEach-Object { Process $_ }
}
```

### 2. Corrected Patterns

```powershell
# ✅ Generic List for dynamic arrays
$results = [System.Collections.Generic.List[object]]::new()
foreach ($item in $items) {
    $results.Add($item)  # O(1) amortized
}

# ✅ Direct processing without wrapping
$data | ForEach-Object { $_ }

# ✅ Pre-computed strings
$timestamp = Get-Date
foreach ($item in $largeCollection) {
    Write-Output "Processing: $($item.Name) at $timestamp"
}

# ✅ Flattened pipeline
$data | Where-Object { $_.Active } | ForEach-Object { Process $_ }
```

## Measurement Tools

### 1. Built-in Measurement

```powershell
# Basic timing
$elapsed = Measure-Command { 
    # Code to measure
}
Write-Host "Elapsed: $($elapsed.TotalMilliseconds)ms"

# Detailed measurement with multiple runs
function Measure-Detailed {
    param(
        [scriptblock]$ScriptBlock,
        [int]$Runs = 10
    )
    
    $times = 1..$Runs | ForEach-Object {
        (Measure-Command { & $ScriptBlock }).TotalMilliseconds
    }
    
    $sorted = $times | Sort-Object
    return @{
        Mean = ($times | Measure-Object -Average).Average
        Median = $sorted[[math]::Floor($sorted.Count / 2)]
        P95 = $sorted[[math]::Floor(0.95 * $sorted.Count)]
        Min = $sorted[0]
        Max = $sorted[-1]
    }
}
```

### 2. Memory Measurement

```powershell
function Measure-MemoryImpact {
    param([scriptblock]$ScriptBlock)
    
    [System.GC]::Collect()
    $before = [System.GC]::GetTotalMemory($false)
    
    $result = & $ScriptBlock
    
    [System.GC]::Collect()
    $after = [System.GC]::GetTotalMemory($false)
    
    return @{
        Result = $result
        MemoryDeltaBytes = $after - $before
        MemoryDeltaMB = ($after - $before) / 1MB
    }
}
```

## PowerShell Performance Checklist

### Pre-Development
- [ ] Choose appropriate data structures for access patterns
- [ ] Plan for memory-efficient processing pipelines
- [ ] Identify opportunities for parallel processing

### During Development
- [ ] Use compiled regex for repeated pattern matching
- [ ] Prefer pipelines over intermediate array creation
- [ ] Use appropriate collections (ArrayList, Generic.List)
- [ ] Minimize string concatenation in loops

### Testing
- [ ] Benchmark critical functions with realistic data sizes
- [ ] Test memory usage with large datasets
- [ ] Validate performance under concurrent execution
- [ ] Measure end-to-end operation timing

### Optimization
- [ ] Profile to identify actual bottlenecks
- [ ] Optimize hot paths first (80/20 rule)
- [ ] Use parallel processing for I/O bound operations
- [ ] Cache expensive computations

## Integration with Strataregula

The PowerShell optimizations integrate with the existing performance infrastructure:

1. **Benchmarking**: Use `perf_suite.py` to compare PowerShell vs Python implementations
2. **Regression Testing**: Include PowerShell benchmarks in CI pipeline
3. **Cross-Language Analysis**: Compare performance characteristics across languages
4. **Historical Tracking**: Store PowerShell performance metrics alongside Python metrics

## Example: Optimized Secret Scanning

```powershell
# Performance-optimized version based on existing secret-audit.ps1
function Invoke-HighPerformanceSecretScan {
    param(
        [string]$ScanPath = ".",
        [int]$Parallelism = 10,
        [switch]$EnableProfiling
    )
    
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Pre-compiled patterns for maximum performance
    $compiledPatterns = @(
        [regex]::new('ghp_[a-zA-Z0-9]{36}', 'Compiled'),
        [regex]::new('gho_[a-zA-Z0-9]{36}', 'Compiled'),
        [regex]::new('AKIA[0-9A-Z]{16}', 'Compiled'),
        [regex]::new('sk-[a-zA-Z0-9]{48}', 'Compiled')
    )
    
    # Efficient file collection
    $files = Get-ChildItem -Path $ScanPath -Recurse -File |
        Where-Object { 
            $_.Length -le 2MB -and 
            $_.Extension -notin @('.exe', '.dll', '.bin', '.jpg', '.png') 
        }
    
    if ($EnableProfiling) {
        Write-Host "Files to scan: $($files.Count)"
        Write-Host "Patterns: $($compiledPatterns.Count)"
    }
    
    # Parallel processing for optimal throughput
    $results = $files | ForEach-Object -Parallel {
        $patterns = $using:compiledPatterns
        
        try {
            $content = [System.IO.File]::ReadAllText($_.FullName)
            
            foreach ($pattern in $patterns) {
                $matches = $pattern.Matches($content)
                foreach ($match in $matches) {
                    @{
                        File = $_.FullName
                        Match = $match.Value
                        Index = $match.Index
                    }
                }
            }
        } catch {
            # Skip files that can't be read
        }
    } -ThrottleLimit $Parallelism
    
    $sw.Stop()
    
    if ($EnableProfiling) {
        Write-Host "Scan completed in: $($sw.Elapsed.TotalMilliseconds)ms"
        Write-Host "Throughput: $([math]::Round($files.Count / $sw.Elapsed.TotalSeconds)) files/second"
    }
    
    return $results
}
```

This optimized implementation leverages:
- Pre-compiled regex patterns
- Efficient file filtering
- Parallel processing for I/O bound operations
- Memory-efficient string handling
- Performance profiling integration
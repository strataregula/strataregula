#!/usr/bin/env pwsh
# StrataRegula Security Pattern Distribution
# Download URL: https://patterns.security-audit.io/scripts/secret-audit.ps1
# Version: 1.0.0
# Cross-platform PowerShell secret detection script

param(
    [string]$ScanPath = ".",
    [switch]$Verbose = $false,
    [string]$ConfigUrl = "https://patterns.security-audit.io/api/v1/rulesets/all.toml"
)

Write-Host "🔍 StrataRegula Security Pattern Scanner v1.0" -ForegroundColor Cyan
Write-Host "Distribution: patterns.security-audit.io" -ForegroundColor Yellow
Write-Host "Scanning path: $ScanPath" -ForegroundColor Yellow

# Download latest patterns if URL provided
if ($ConfigUrl -and $ConfigUrl.StartsWith("http")) {
    Write-Host "⬇️ Downloading latest patterns from: $ConfigUrl" -ForegroundColor Yellow
    try {
        $tempConfig = [System.IO.Path]::GetTempFileName() + ".toml"
        Invoke-WebRequest -Uri $ConfigUrl -OutFile $tempConfig -UseBasicParsing
        Write-Host "✅ Patterns downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Failed to download patterns, using built-in rules: $($_.Exception.Message)" -ForegroundColor Yellow
        $tempConfig = $null
    }
}

$secretPatterns = @(
    @{Pattern = 'ghp_[a-zA-Z0-9]{36}'; Description = 'GitHub Personal Access Token'},
    @{Pattern = 'gho_[a-zA-Z0-9]{36}'; Description = 'GitHub OAuth Token'},
    @{Pattern = 'ghu_[a-zA-Z0-9]{36}'; Description = 'GitHub User-to-Server Token'},
    @{Pattern = 'ghs_[a-zA-Z0-9]{36}'; Description = 'GitHub Server-to-Server Token'},
    @{Pattern = 'AKIA[0-9A-Z]{16}'; Description = 'AWS Access Key ID'},
    @{Pattern = 'sk-[a-zA-Z0-9]{48}'; Description = 'OpenAI API Key'},
    @{Pattern = 'sk-ant-api[0-9]{2}-[A-Za-z0-9\-_]{95}'; Description = 'Anthropic Claude API Key'},
    @{Pattern = 'xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}'; Description = 'Slack Bot Token'},
    @{Pattern = 'Bearer\s+[a-zA-Z0-9+/=]{20,}'; Description = 'Bearer Token'},
    @{Pattern = '-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'; Description = 'Private Key'},
    @{Pattern = 'eyJ[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+'; Description = 'JWT Token'}
)

$detectedSecrets = @()
$scannedFiles = 0

# Enhanced exclusion patterns
$excludePatterns = @(
    '*.pyc', '__pycache__', '.git', 'node_modules', '.pytest_cache',
    '.coverage', '*.egg-info', 'dist', 'build', '.cache', '.nyc_output',
    'coverage', 'logs', 'reports'
)

function Should-ExcludeFile {
    param($FilePath)
    
    # Size limit: Skip files larger than 2MB
    try {
        $fileInfo = Get-Item $FilePath -ErrorAction SilentlyContinue
        if ($fileInfo -and $fileInfo.Length -gt 2MB) {
            return $true
        }
    } catch {
        return $true
    }
    
    # Binary file exclusion
    $binaryExtensions = @('.exe', '.dll', '.bin', '.so', '.dylib', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz')
    $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
    if ($extension -in $binaryExtensions) {
        return $true
    }
    
    # Pattern-based exclusion
    foreach ($pattern in $excludePatterns) {
        if ($FilePath -like "*$pattern*") {
            return $true
        }
    }
    return $false
}

if (Test-Path $ScanPath) {
    Get-ChildItem -Path $ScanPath -Recurse -File | Where-Object {
        -not (Should-ExcludeFile $_.FullName)
    } | ForEach-Object {
        $file = $_
        $scannedFiles++
        
        if ($Verbose) {
            Write-Host "  Scanning: $($file.FullName)" -ForegroundColor Gray
        }
        
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        
        if ($content) {
            foreach ($pattern in $secretPatterns) {
                $matches = [regex]::Matches($content, $pattern.Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                
                if ($matches.Count -gt 0) {
                    foreach ($match in $matches) {
                        $detectedSecrets += @{
                            File = $file.FullName
                            RelativePath = $file.FullName.Replace((Get-Location).Path, "").TrimStart('\', '/')
                            Type = $pattern.Description
                            Match = $match.Value
                            Line = ($content.Substring(0, $match.Index) -split "`n").Count
                        }
                    }
                }
            }
        }
    }
} else {
    Write-Host "⚠️  Path not found: $ScanPath" -ForegroundColor Yellow
}

# Cleanup temp config
if ($tempConfig -and (Test-Path $tempConfig)) {
    Remove-Item $tempConfig -Force
}

Write-Host "`n📊 Scan Results:" -ForegroundColor Green
Write-Host "Files scanned: $scannedFiles" -ForegroundColor White
Write-Host "Secrets detected: $($detectedSecrets.Count)" -ForegroundColor White

if ($detectedSecrets.Count -gt 0) {
    Write-Host "`n🚨 SECRETS DETECTED:" -ForegroundColor Red
    foreach ($secret in $detectedSecrets) {
        Write-Host "  File: $($secret.RelativePath)" -ForegroundColor Red
        Write-Host "  Type: $($secret.Type)" -ForegroundColor Yellow
        Write-Host "  Line: $($secret.Line)" -ForegroundColor Gray
        Write-Host "  Match: $($secret.Match.Substring(0, [Math]::Min(50, $secret.Match.Length)))..." -ForegroundColor Magenta
        Write-Host ""
    }
    
    Write-Host "🔧 Remediation Steps:" -ForegroundColor Yellow
    Write-Host "1. Remove or replace detected secrets with environment variables" -ForegroundColor White
    Write-Host "2. Add secrets to .gitignore to prevent future commits" -ForegroundColor White
    Write-Host "3. Rotate any exposed credentials immediately" -ForegroundColor White
    Write-Host "4. Use GitHub Secrets for CI/CD workflows" -ForegroundColor White
    Write-Host "5. Update patterns: https://patterns.security-audit.io" -ForegroundColor White
    
    exit 1
} else {
    Write-Host "✅ No secrets detected - Repository is secure" -ForegroundColor Green
    Write-Host "🔄 Pattern updates available at: https://patterns.security-audit.io" -ForegroundColor Cyan
    exit 0
}
#!/usr/bin/env pwsh
# Secret Detection Script for strataregula
# Scans configuration files and source code for potential secrets

param(
    [string]$ScanPath = ".",
    [switch]$Verbose = $false
)

Write-Host "🔍 Secret Detection Scan - strataregula" -ForegroundColor Cyan
Write-Host "Scanning path: $ScanPath" -ForegroundColor Yellow

$secretPatterns = @(
    @{Pattern = 'ghp_[a-zA-Z0-9]{36}'; Description = 'GitHub Personal Access Token'},
    @{Pattern = 'gho_[a-zA-Z0-9]{36}'; Description = 'GitHub OAuth Token'},
    @{Pattern = 'ghu_[a-zA-Z0-9]{36}'; Description = 'GitHub User-to-Server Token'},
    @{Pattern = 'ghs_[a-zA-Z0-9]{36}'; Description = 'GitHub Server-to-Server Token'},
    @{Pattern = 'AKIA[0-9A-Z]{16}'; Description = 'AWS Access Key ID'},
    @{Pattern = 'sk-[a-zA-Z0-9]{48}'; Description = 'OpenAI API Key'},
    @{Pattern = 'xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}'; Description = 'Slack Bot Token'},
    @{Pattern = 'Bearer\s+[a-zA-Z0-9+/=]{20,}'; Description = 'Bearer Token'},
    @{Pattern = '-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'; Description = 'Private Key'},
    @{Pattern = 'eyJ[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+\.[a-zA-Z0-9+/=]+'; Description = 'JWT Token'}
)

$detectedSecrets = @()
$scannedFiles = 0

# Exclude patterns to avoid false positives
$excludePatterns = @(
    '*.pyc',
    '__pycache__',
    '.git',
    'node_modules',
    '.pytest_cache',
    '.coverage',
    '*.egg-info',
    'dist',
    'build',
    '.cache'
)

function Should-ExcludeFile {
    param($FilePath)
    
    # サイズ制限: 2MB以上のファイルはスキップ
    try {
        $fileInfo = Get-Item $FilePath -ErrorAction SilentlyContinue
        if ($fileInfo -and $fileInfo.Length -gt 2MB) {
            return $true
        }
    } catch {
        return $true
    }
    
    # バイナリファイルの除外
    $binaryExtensions = @('.exe', '.dll', '.bin', '.so', '.dylib', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz')
    $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
    if ($extension -in $binaryExtensions) {
        return $true
    }
    
    # 既存のパターン除外
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
    
    exit 1
} else {
    Write-Host "✅ No secrets detected - Repository is secure" -ForegroundColor Green
    exit 0
}
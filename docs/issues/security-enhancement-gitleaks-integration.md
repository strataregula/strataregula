# [0.4] セキュリティ強化 - GitLeaks完全統合

**Labels**: `backlog`, `target-0.4`, `security`, `enhancement`, `priority-p1`  
**Milestone**: `v0.4.0`  
**Priority**: P1 (高価値実装)

## 📋 目的
現在のPowerShell `secret-audit.ps1` とGitLeaksを統合し、ハイブリッド検出システムを構築する。False positive完全排除と検出パターン拡充により、DevContainerデプロイメント時のセキュリティを最高水準まで向上させる。

## 🎯 具体的な仕様

### 統合アーキテクチャ設計
```
Security Scanning Pipeline
├─ PowerShell Layer (Fast Pre-scan)
│  ├─ Regex-based token detection
│  ├─ File type filtering  
│  └─ Allowlist pre-filtering
├─ GitLeaks Layer (Deep Analysis)
│  ├─ Advanced pattern matching
│  ├─ Context analysis
│  └─ Entropy-based detection
└─ Report Consolidation
   ├─ Duplicate elimination
   ├─ Severity scoring
   └─ Unified output format
```

### CLI設計
```bash
# 統合セキュリティスキャン
python -m security.tools.sec_scan --hybrid --config .security.yaml

# 個別ツール実行
python -m security.tools.sec_scan --powershell-only
python -m security.tools.sec_scan --gitleaks-only  

# CI統合用
python -m security.tools.sec_scan --ci --output security_report.json

# 詳細設定
python -m security.tools.sec_scan \
  --config .security.yaml \
  --allowlist security-allowlist.yaml \
  --gitleaks-config .gitleaks.toml \
  --output-format json \
  --severity-threshold medium
```

## 🔧 技術仕様

### 統合設定ファイル
```yaml
# .security.yaml (新規)
version: 1
scanning:
  enabled_scanners:
    - powershell
    - gitleaks
  
powershell:
  script_path: "secret-audit.ps1"
  allowlist_path: "security-allowlist.yaml" 
  timeout_seconds: 300
  
gitleaks:
  config_path: ".gitleaks.toml"
  report_format: "json"
  timeout_seconds: 600
  additional_args: ["--verbose"]

output:
  format: "json"  # json, markdown, console
  consolidate_duplicates: true
  severity_levels: ["critical", "high", "medium", "low"]
  
filtering:
  exclude_paths:
    - "tests/security/fixtures/"
    - "docs/security/examples/"
  exclude_extensions: [".md", ".txt", ".log"]
  
notification:
  fail_on_critical: true
  fail_on_high: true
  fail_on_medium: false
```

### GitLeaks設定最適化
```toml
# .gitleaks.toml (拡張)
title = "Strataregula Security Configuration"

[extend]
useDefault = true

[[rules]]
description = "Strataregula API Keys"
id = "strataregula-api-key"
regex = '''(?i)(strataregula[_-]?api[_-]?key\s*[:=]\s*['"']?)([a-zA-Z0-9]{32,})'''
tags = ["key", "api", "strataregula"]
severity = "high"

[[rules]]
description = "Performance Benchmark Tokens"
id = "benchmark-token"
regex = '''(?i)(bench[_-]?token\s*[:=]\s*['"']?)([a-zA-Z0-9]{16,})'''
tags = ["token", "benchmark"]
severity = "medium"

[[rules]]
description = "DevContainer Registry Keys"
id = "devcontainer-registry"
regex = '''(?i)(registry[_-]?key\s*[:=]\s*['"']?)([a-zA-Z0-9+/]{20,}={0,2})'''
tags = ["registry", "devcontainer"]
severity = "critical"

[allowlist]
commits = []
paths = [
    "tests/security/fixtures/",
    "docs/security/examples/",
    "SECURITY_AUDIT_TRAIL.md"
]
regexes = [
    "AKIAIOSFODNN7EXAMPLE",
    "ghp_123456789012345678901234567890123456",
    "sk-test_123456789012345678901234567890",
    "benchmark_test_token_not_real_12345"
]
```

### 統合スキャナー実装
```python
# security/tools/sec_scan.py
import asyncio
import json
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SecurityFinding:
    scanner: str  # "powershell" | "gitleaks"
    severity: str
    rule_id: str
    description: str
    file_path: str
    line_number: int
    match_text: str
    confidence: float

class HybridSecurityScanner:
    def __init__(self, config_path: str = ".security.yaml"):
        self.config = self.load_config(config_path)
        self.findings: List[SecurityFinding] = []
    
    async def scan_hybrid(self) -> Dict[str, Any]:
        """PowerShell + GitLeaks ハイブリッドスキャン"""
        tasks = []
        
        if "powershell" in self.config.enabled_scanners:
            tasks.append(self.run_powershell_scan())
            
        if "gitleaks" in self.config.enabled_scanners:
            tasks.append(self.run_gitleaks_scan())
            
        results = await asyncio.gather(*tasks)
        consolidated = self.consolidate_findings(results)
        
        return self.generate_report(consolidated)
    
    async def run_powershell_scan(self) -> List[SecurityFinding]:
        """PowerShell secret-audit.ps1 実行"""
        cmd = [
            "powershell", "-File", self.config.powershell.script_path,
            "-ScanPath", ".",
            "-AllowlistPath", self.config.powershell.allowlist_path,
            "-OutputFormat", "json"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"PowerShell scan failed: {stderr.decode()}")
            
        return self.parse_powershell_output(stdout.decode())
    
    async def run_gitleaks_scan(self) -> List[SecurityFinding]:
        """GitLeaks実行"""
        cmd = [
            "gitleaks", "detect",
            "--source", ".",
            "--config", self.config.gitleaks.config_path,
            "--report-format", "json",
            "--no-git"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # GitLeaksは検出時にexit code 1を返すため、正常な動作
        if process.returncode > 1:
            raise Exception(f"GitLeaks scan failed: {stderr.decode()}")
            
        return self.parse_gitleaks_output(stdout.decode())
    
    def consolidate_findings(self, scanner_results: List[List[SecurityFinding]]) -> List[SecurityFinding]:
        """重複排除と統合"""
        all_findings = []
        for results in scanner_results:
            all_findings.extend(results)
        
        # 重複排除ロジック (ファイルパス + 行番号 + マッチテキスト)
        unique_findings = {}
        for finding in all_findings:
            key = f"{finding.file_path}:{finding.line_number}:{finding.match_text}"
            if key not in unique_findings or finding.confidence > unique_findings[key].confidence:
                unique_findings[key] = finding
                
        return list(unique_findings.values())
```

## 📊 成功指標

### セキュリティ要件
- **False Positive Rate**: 0件 (現在達成済み)
- **Detection Coverage**: > 95% (エントロピーベース検出追加)
- **Scan Speed**: PowerShell単体比 < 150% (並列実行効果)
- **CI Integration**: < 3分 (現在の2倍以内)

### 品質要件
- ✅ 15+ token/key pattern対応
- ✅ Context-aware false positive elimination
- ✅ Severity-based CI gate integration
- ✅ 統合レポート生成 (JSON/Markdown/Console)

### 運用要件
- ✅ Zero-configuration default設定
- ✅ 段階的移行サポート (PowerShell単体→ハイブリッド)
- ✅ CI/CD pipeline seamless integration
- ✅ Historical audit trail maintenance

## 🔄 GitHubワークフロー統合

### 新しいセキュリティワークフロー
```yaml
# .github/workflows/security-hybrid.yml
name: Hybrid Security Scanning
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # GitLeaks full history scan
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Dependencies
        run: |
          pip install -e .
          # GitLeaks installation
          curl -sSL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_linux_x64.tar.gz | tar xz
          sudo mv gitleaks /usr/local/bin/
          
      - name: Install PowerShell
        run: |
          wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
          sudo dpkg -i packages-microsoft-prod.deb
          sudo apt-get update
          sudo apt-get install -y powershell
          
      - name: Run Hybrid Security Scan
        run: |
          python -m security.tools.sec_scan \
            --hybrid \
            --config .security.yaml \
            --output security_report.json \
            --ci
            
      - name: Upload Security Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: |
            security_report.json
            security_report.md
            
      - name: Security Gate Check
        run: |
          # Critical/High findings で fail
          python -c "
          import json
          with open('security_report.json') as f:
              report = json.load(f)
          critical = len([f for f in report['findings'] if f['severity'] == 'critical'])
          high = len([f for f in report['findings'] if f['severity'] == 'high'])
          if critical > 0 or high > 0:
              print(f'Security gate failed: {critical} critical, {high} high severity findings')
              exit(1)
          print('Security gate passed')
          "
```

### PR統合
```yaml
      - name: Comment PR with Security Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('security_report.json'));
            
            let body = '## 🔒 Security Scan Results\n\n';
            
            if (report.summary.total_findings === 0) {
              body += '✅ **No security issues detected**\n\n';
            } else {
              body += `⚠️  **${report.summary.total_findings} findings detected**\n\n`;
              body += `| Severity | Count |\n|----------|-------|\n`;
              Object.entries(report.summary.by_severity).forEach(([severity, count]) => {
                body += `| ${severity} | ${count} |\n`;
              });
            }
            
            body += '\n*Powered by PowerShell + GitLeaks hybrid scanning*';
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## 🔗 段階的移行戦略

### Phase 1: 基盤構築 (Week 1-2)
1. `HybridSecurityScanner`クラス実装
2. `.security.yaml`設定システム構築
3. PowerShell→Python呼び出し統合
4. 基本的な統合テスト

### Phase 2: GitLeaks統合 (Week 2-3)
1. GitLeaks実行・結果解析実装
2. `.gitleaks.toml`最適化・拡張
3. 重複排除・統合アルゴリズム
4. 並列実行システム構築

### Phase 3: レポート・CI統合 (Week 3-4)
1. 統合レポート生成システム
2. CI workflow更新・テスト
3. PR comment自動生成
4. Security gate設定

### Phase 4: 最適化・運用化 (Week 4)
1. パフォーマンス最適化
2. エラーハンドリング強化
3. ドキュメント・移行ガイド整備
4. 監視・アラート設定

## 🚫 非目標・制限事項

### 現在のスコープ外
- **リアルタイム監視**: バッチスキャンのみ
- **自動修正機能**: 検出のみ、修正は手動
- **サードパーティ統合**: GitLeaks以外のツール
- **暗号化解析**: 平文パターンマッチングのみ
- **ネットワークスキャン**: ファイルシステムのみ

### 制約事項
- **GitLeaks依存**: GitLeaksのインストールが前提
- **PowerShell要件**: PowerShell Core利用可能環境
- **メモリ使用量**: 大規模リポジトリでの制限
- **実行時間**: 完全スキャンは数分要する場合

## 🔗 関連・依存 Issues

### 前提条件
- ✅ PowerShell secret-audit.ps1 最適化完了 (0.3.0)
- ✅ security-allowlist.yaml システム (0.3.0)
- ✅ False positive 0件達成 (0.3.0)

### 連携推奨
- **CI完全統合** (P0) - Security gate組み込み
- **DevContainer Security** - Container registry key検出
- **Performance Tools** - Security scan性能測定

### 後続展開
- **Security Dashboard** (0.5.0) - Web UI統合
- **Automated Remediation** (0.5.0) - 自動修正提案
- **Compliance Reporting** (0.5.0) - 監査レポート生成

## ✅ 完了条件 (Definition of Done)

### 技術要件
- [ ] PowerShell + GitLeaks ハイブリッドスキャン動作
- [ ] 重複排除・統合アルゴリズム検証
- [ ] 3種類出力形式 (JSON/Markdown/Console) 対応
- [ ] CI workflow統合・テスト完了
- [ ] False positive rate 0%維持

### 品質要件
- [ ] 単体テスト Coverage > 90%
- [ ] 統合テスト (実際のリポジトリ)
- [ ] パフォーマンステスト (大規模スキャン)
- [ ] セキュリティテスト (既知の脆弱性検出)

### 運用要件
- [ ] 段階的移行ガイド作成
- [ ] 設定ファイル・ベストプラクティス整備
- [ ] トラブルシューティング手順
- [ ] 監視・アラート設定手順

### セキュリティ要件
- [ ] 既知token/keyパターン 100%検出
- [ ] エントロピーベース検出機能確認
- [ ] Allowlist機能完全動作
- [ ] Audit trail完整性確保

---

**推定工数**: 3-4 weeks  
**担当者**: Security Team  
**レビュワー**: Security Engineering + DevOps  
**作成日**: 2025-09-01  
**最終更新**: 2025-09-01
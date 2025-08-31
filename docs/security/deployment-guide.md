# StrataRegula セキュリティシステム展開ガイド

**対象**: 開発チーム・DevOpsエンジニア  
**目的**: TOKEN・機密情報検知システムの完全展開  
**最終更新**: 2025-08-31

---

## 🎯 セキュリティシステム概要

StrataRegula に以下の **多層防御セキュリティシステム** を実装：

### 🛡️ 防御レイヤー
1. **ローカル防御**: Pre-commit hooks（開発者PC）
2. **リポジトリ防御**: .gitignore 強化（Gitレベル）
3. **CI防御**: GitHub Actions 自動スキャン（PRレベル）
4. **多重検証**: PowerShell + GitLeaks（デュアルエンジン）

---

## 📋 展開チェックリスト

### ✅ Phase 1: ファイル確認
展開されたセキュリティファイル：

```
strataregula/
├── 🔒 secret-audit.ps1              # PowerShell秘密検知エンジン
├── 🔒 .github/workflows/security.yml # 統合セキュリティCI
├── 🔒 .github/gitleaks.toml         # GitLeaks設定
├── 🔒 .pre-commit-config.yaml       # ローカルフック
├── 🔒 .gitignore.security           # 強化版gitignore
├── 📋 docs/security/audit-trail.md  # セキュリティ監査記録
└── 📋 docs/security/deployment-guide.md # このファイル
```

### ✅ Phase 2: ローカル環境セットアップ

#### 1. Pre-commit インストール
```bash
# Python環境にpre-commitをインストール
pip install pre-commit

# リポジトリでフックを有効化
cd strataregula
pre-commit install

# 全ファイルでテスト実行
pre-commit run --all-files
```

#### 2. PowerShell 実行権限設定（Windows）
```powershell
# PowerShell実行ポリシーの確認
Get-ExecutionPolicy

# 必要に応じてポリシー変更（管理者権限）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# スクリプト実行テスト
./secret-audit.ps1 -ScanPath . -Verbose
```

### ✅ Phase 3: CI/CD 動作確認

#### 1. GitHub Actions 確認
```bash
# セキュリティワークフローの確認
git add .
git commit -m "test: security system deployment"
git push origin feature/security-test

# PRを作成してCIトリガーを確認
```

#### 2. セキュリティスキャン結果の確認
- **GitLeaks**: 業界標準パターン検知
- **PowerShell**: StrataRegula専用パターン検知
- **Security Summary**: 統合結果レポート

---

## 🔧 動作テスト

### テスト1: ローカル検知テスト
```bash
# テスト用ファイル作成（危険：実際のトークンは使用禁止）
echo "github_token=ghp_1234567890123456789012345678901234567890" > test_secret.txt

# PowerShell検知テスト
./secret-audit.ps1 -ScanPath . -Verbose

# Pre-commit検知テスト
git add test_secret.txt
git commit -m "test commit"  # ← ここでブロックされるはず

# テストファイル削除
rm test_secret.txt
```

### テスト2: CI検知テスト
```bash
# 安全なテスト（文字列分割でパターン回避）
echo 'test_var="gh" + "p_" + "fake123456789012345678901234567890"' > safe_test.py
git add safe_test.py
git commit -m "test: CI security detection"
git push origin test-branch
# PR作成してCIの動作確認
```

---

## 🚨 緊急時対応

### シナリオ1: 秘密情報が検知された場合
```bash
# 1. 即座にファイルから秘密情報を削除
vim [検知されたファイル]

# 2. 該当する認証情報をローテーション
# GitHub: Settings > Developer settings > Personal access tokens
# AWS: IAM > Access keys > Deactivate
# OpenAI: API keys > Revoke

# 3. Gitヒストリから完全削除（必要に応じて）
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch [ファイル名]' \
--prune-empty --tag-name-filter cat -- --all

# 4. 強制プッシュ（チーム合意必要）
git push origin --force --all
```

### シナリオ2: CI が誤検知する場合
```bash
# 1. 誤検知パターンをallowlistに追加
vim .github/gitleaks.toml

# 2. allowlist例
[[allowlist]]
description = "Documentation examples"
regexes = [
    '''example_token_pattern_here''',
]

# 3. 設定コミット・プッシュ
git add .github/gitleaks.toml
git commit -m "fix: update security allowlist"
git push
```

---

## ⚙️ カスタマイゼーション

### PowerShell パターン追加
```powershell
# secret-audit.ps1 の $secretPatterns に追加
@{Pattern = 'custom_pattern_here'; Description = 'Custom Token Type'}
```

### GitLeaks ルール追加
```toml
# .github/gitleaks.toml に追加
[[rules]]
id = "custom-rule"
description = "Custom Rule Description"
regex = '''custom_regex_pattern'''
tags = ["custom", "token"]
```

### Pre-commit フック追加
```yaml
# .pre-commit-config.yaml に追加
- repo: https://github.com/custom/hook
  rev: v1.0.0
  hooks:
    - id: custom-security-check
```

---

## 📊 セキュリティメトリクス

### 監視すべき指標
- **検知率**: 月間秘密情報検知件数
- **誤検知率**: False positive の割合
- **修正時間**: 検知から修正完了までの時間
- **カバレッジ**: スキャン対象ファイル数・パターン数

### レポート生成
```bash
# セキュリティスキャン実行ログ
./secret-audit.ps1 -ScanPath . > security_scan_$(date +%Y%m%d).log

# GitLeaks詳細レポート
gitleaks detect --config .github/gitleaks.toml --report-format json --report-path security_report.json
```

---

## 🔄 定期メンテナンス

### 月次タスク
- [ ] セキュリティパターンの更新
- [ ] 誤検知パターンの見直し
- [ ] 新しい脅威パターンの追加
- [ ] チーム向けセキュリティ教育

### 四半期タスク
- [ ] セキュリティツールのバージョンアップ
- [ ] 全リポジトリのセキュリティ監査
- [ ] インシデント対応手順の見直し
- [ ] 外部セキュリティ評価の実施

---

## 📞 サポート・連絡先

### 技術的な問題
- **PowerShell スクリプト**: 開発チームに連絡
- **GitHub Actions**: DevOps チームに連絡
- **Pre-commit issues**: ローカル環境担当者に連絡

### セキュリティインシデント
- **緊急度高**: 即座にテックリードに報告
- **緊急度中**: 24時間以内にセキュリティチームに報告
- **緊急度低**: 週次ミーティングで共有

---

## ✅ 展開完了確認

### 全チームメンバーが以下を確認：
- [ ] ローカル環境で pre-commit が動作する
- [ ] PowerShell スクリプトが実行できる
- [ ] テストコミットでセキュリティチェックが動作する
- [ ] GitHub Actions でセキュリティスキャンが実行される
- [ ] セキュリティインシデント対応手順を理解している

---

**🎉 セキュリティシステム展開完了！**

StrataRegula は業界最高水準の多層防御セキュリティシステムにより保護されています。全開発者が安心して開発に集中できる環境が整いました。
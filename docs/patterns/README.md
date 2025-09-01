# StrataRegula Security Patterns Distribution

**配布URL**: `https://patterns.security-audit.io` (GitHub Pages)  
**更新頻度**: コミット時自動更新  
**バージョン**: v1.0 (2025-08-31)

---

## 🚀 クイックスタート

### 1. PowerShell スクリプト直接実行
```bash
# 最新版のダウンロード・実行
curl -s https://patterns.security-audit.io/scripts/secret-audit.ps1 | pwsh
```

### 2. GitLeaks ルールセット
```bash
# 全ルールセット
gitleaks detect --config https://patterns.security-audit.io/api/v1/rulesets/all.toml

# 特定パターンのみ
gitleaks detect --config https://patterns.security-audit.io/api/v1/rulesets/secrets.toml
gitleaks detect --config https://patterns.security-audit.io/api/v1/rulesets/aws.toml
gitleaks detect --config https://patterns.security-audit.io/api/v1/rulesets/github.toml
```

### 3. GitHub Actions での使用
```yaml
# .github/workflows/security.yml
- name: Run security scan
  uses: gitleaks/gitleaks-action@v2
  with:
    config: https://patterns.security-audit.io/api/v1/rulesets/all.toml
```

---

## 📋 利用可能なパターンセット

| パターンセット | 用途 | URL |
|-------------|------|-----|
| **all.toml** | 包括的スキャン | `/api/v1/rulesets/all.toml` |
| **secrets.toml** | 一般的な秘密情報 | `/api/v1/rulesets/secrets.toml` |
| **github.toml** | GitHub固有パターン | `/api/v1/rulesets/github.toml` |
| **aws.toml** | AWS認証情報 | `/api/v1/rulesets/aws.toml` |
| **openai.toml** | OpenAI APIキー | `/api/v1/rulesets/openai.toml` |

---

## 🛠️ API エンドポイント

### パターンセット取得
```bash
GET https://patterns.security-audit.io/api/v1/rulesets/manifest.json
GET https://patterns.security-audit.io/api/v1/rulesets/{pattern}.toml
```

### スクリプト取得
```bash
GET https://patterns.security-audit.io/scripts/secret-audit.ps1
GET https://patterns.security-audit.io/scripts/deploy.sh
```

---

## 🔄 更新情報

### v1.0 (2025-08-31)
- 初回リリース
- 10種類の秘密検知パターン
- GitHub/AWS/OpenAI/JWT対応
- PowerShell + GitLeaks デュアルエンジン

### 更新通知
GitHub リポジトリの Watch 設定で最新パターンの追加通知を受け取れます。

---

## 📞 サポート

- **GitHub Issues**: パターン追加要望・バグ報告
- **Discord**: リアルタイムサポート (準備中)
- **Email**: security@strataregula.com

---

## 🔐 セキュリティポリシー

- 全パターンはオープンソース
- 定期的なセキュリティ監査実施
- False Positive の継続的改善
- コミュニティフィードバックの反映

**配布元**: [StrataRegula Security Team](https://github.com/strataregula/security-patterns)
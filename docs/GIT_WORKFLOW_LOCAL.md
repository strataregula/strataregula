# ローカル環境でのGit作業管理ガイド

**目的**: ローカル環境でのGit作業を効率的に管理し、将来のアップロード時に備える

---

## 📋 現在の環境状況

- **リポジトリ**: strataregula/strataregula
- **SSH設定**: `github.com-strataregula` で認証済み
- **制約**: ローカル環境のためpush不可
- **作業**: オンボーディング文書システム開発

---

## 🔧 ローカル作業フロー

### 1. ブランチ管理

```bash
# 現在のブランチ確認
git branch

# 作業用ブランチ作成
git checkout -b feature/onboarding-docs-system

# 変更をステージング
git add docs/

# ローカルコミット
git commit -m "docs: create comprehensive onboarding system

- Add ONBOARDING.md with 30-minute contribution guide
- Create environment setup documentation (SETUP.md)
- Add troubleshooting guide with common issues
- Implement Mermaid flow visualization
- Sync Python version requirements across docs"
```

### 2. 作業記録管理

#### 完了した作業
- ✅ `docs/ONBOARDING.md` - 新規参加者ガイド
- ✅ `docs/environment/SETUP.md` - 環境構築ガイド
- ✅ `docs/environment/TROUBLESHOOTING.md` - トラブルシューティング
- ✅ `docs/environment/DEVCONTAINER.md` - DevContainer ガイド
- ✅ `docs/RELEASE_CHECKLIST.md` - リリース品質管理
- ✅ `docs/GOLDEN_METRICS_GUARD.md` - パフォーマンス回帰検知
- ✅ README.md への導線追加
- ✅ Python バージョン要件統一
- ✅ 実地テスト完了 & フィードバック反映

---

## 🗂️ ファイル構成

```
docs/
├── ONBOARDING.md              # 新規参加者30分ガイド
├── RELEASE_CHECKLIST.md       # リリース品質管理
├── GOLDEN_METRICS_GUARD.md    # パフォーマンス回帰検知
└── environment/
    ├── SETUP.md               # 15分環境構築
    ├── TROUBLESHOOTING.md     # 症状別トラブル解決
    └── DEVCONTAINER.md        # チーム環境統一

README.md                      # 新規参加者導線追加
.development-rules.md          # バージョン情報更新(0.3.0)
```

---

## 📊 品質検証結果

### 実地テスト完了
- **Phase 1**: 環境構築（目標15分） ✅
- **Phase 2**: プロジェクト理解（目標10分） ✅  
- **Phase 3**: 作業準備（目標5分） ✅

### 発見・改善事項
1. **Python バージョン統一**: 3.8+ → 3.11+ に統一
2. **バージョン情報更新**: 0.1.1 → 0.3.0 に修正
3. **pytest エラー対処**: __pycache__ 問題の解決法追加
4. **クリーン環境推奨**: ONBOARDING.md に注意事項追加

---

## 🚀 将来のアップロード準備

### PR作成準備コマンド
```bash
# ブランチの確認
git status
git log --oneline -5

# 差分確認
git diff origin/main...HEAD

# PR用の説明準備
echo "## Summary
Complete onboarding documentation system for 30-minute contribution

## Changes  
- Add comprehensive new contributor guide with visual flow
- Create environment setup and troubleshooting documentation
- Establish release quality checklist and performance guard
- Fix Python version inconsistencies and documentation gaps

## Testing
- Real-world onboarding simulation completed
- All phases (15min + 10min + 5min) validated
- Issues discovered and addressed

Based on actual user experience testing." > PR_DESCRIPTION.md
```

---

## 🎯 次回アップロード時の手順

### 1. 事前チェック
```bash
# リモートの最新を取得
git fetch origin

# コンフリクトチェック
git merge-base HEAD origin/main

# ファイル存在確認
ls -la docs/
```

### 2. Push実行
```bash
# ブランチをプッシュ
git push origin feature/onboarding-docs-system

# PR作成（GitHub CLI使用時）
gh pr create --title "docs: complete onboarding system for 30-minute contribution" --body-file PR_DESCRIPTION.md
```

---

## 📋 チェックリスト

### アップロード前確認
- [ ] 全ファイルがコミット済み
- [ ] コミットメッセージが適切
- [ ] PR説明文準備完了
- [ ] テスト結果・改善点を記録済み
- [ ] ファイル構成が整理済み

### アップロード後確認  
- [ ] PR作成確認
- [ ] CI/CD パス確認
- [ ] レビュー対応準備

---

## 🔍 トラブルシューティング

### SSH接続問題
```bash
# 接続テスト
ssh -T github.com-strataregula

# 設定確認
cat ~/.ssh/config | grep -A5 "github.com-strataregula"
```

### リモート設定問題
```bash
# 現在のリモート確認
git remote -v

# 正しい設定
git remote set-url origin github.com-strataregula:strataregula/strataregula.git
```

---

**作成日**: 2025-09-02  
**最終更新**: 2025-09-02  
**ステータス**: 完成・アップロード待ち
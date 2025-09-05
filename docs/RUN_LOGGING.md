# Run Logging Guide

StrataRegula では、**すべての実行（CI / ローカル）を可視化する Runログ**を必須とします。  
Runログは開発の心臓部であり、妥協せず「再現性・透明性・信頼性」を確保します。

---

## 📂 出力場所
- `docs/run/` : JST タイムスタンプ付き Runログ本体 (`YYYYMMDD-HHMM-JST[-label].md`)
- `docs/changes/` : 差分/パッチ/作業ツリー
  - `<timestamp>.patch` : 最新コミットとの差分
  - `<timestamp>.summary.txt` : 差分要約
  - `<timestamp>.wtree.txt` : 作業ツリー状態

---

## 🛠️ 生成方法

### ローカル実行
```bash
python tools/new_run_log.py \
  --label "dev" \
  --summary "ローカルテスト実行" \
  --intent  "設定変更の影響を確認" \
  --with-bench
```

### CI実行
- `test.yml` や `quality-checks.yml` の最後で自動生成
- Artifacts に保存 & PR にサマリをコメント

---

## 🧩 Runログの内容

### 必須セクション
- **Summary**: 実行の結果を3-5行で
- **Intent**: なぜその実行をしたのか
- **PR Context**: PR情報（可能な場合）
- **Git Status**: 現在の作業ツリー状況
- **Recent Commits**: 最新5コミット

### 実行結果セクション  
- **Commands & Results**: 実行したコマンドと結果
  - pytest (quick tests)
  - pytest with coverage
  - CLI verification
  - benchmarks (optional)
- **Key Outputs**: 各種チェック結果サマリ
- **Artifacts**: この実行で生成されたファイル

### 分析・次アクションセクション
- **Git Diff Summary**: 変更の要約
- **Next Actions**: TODO / レビュー依頼など

---

## ✅ 実運用ルール

1. **PRごとに最低1つの Runログを残すこと**
2. **Summary/Intent を必須入力**（空の場合はスクリプトが終了）
3. **CIの実行結果を必ず artifact として保存**
4. **レビュー時は PR コメントに Runログの場所を明示**
5. **ローカルでもリスクの高い変更前後はRunログを作成**

## 📁 ファイル管理ポリシー

### docs/run/ の git 管理
- **通常運用**: `docs/run/` は `.gitignore` で除外、Artifacts経由で共有
- **リリース時**: 重要なRunログのみ main ブランチにコミット可能
- **履歴保持**: 長期保存が必要なRunログは手動でコミット

### Artifact 保存期間
- **PR用**: 30日間（GitHub デフォルト）
- **リリース用**: 永続保存が必要な場合は別途バックアップ

---

## 🎯 使用例

### 開発時
```bash
# 機能開発開始時
python tools/new_run_log.py \
  --label "start-feature-auth" \
  --summary "認証機能の実装を開始" \
  --intent "JWT実装前のベースライン確認"

# テスト修正後
python tools/new_run_log.py \
  --label "fix-tests" \
  --summary "認証関連テストを修正" \
  --intent "CI通過を確認"
```

### リリース時
```bash
# リリース準備
python tools/new_run_log.py \
  --label "release-prep" \
  --summary "v0.3.0リリース準備完了" \
  --intent "全テスト通過とベンチマーク確認" \
  --with-bench
```

---

## 🔧 トラブルシューティング

### Windows環境でのエンコーディングエラー
- 症状: UnicodeEncodeError (cp932)
- 対処: 環境変数 `PYTHONIOENCODING=utf-8` を設定

### pytest が見つからない
- 症状: 'pytest' is not recognized
- 対処: `pip install -e ".[test]"` または `pip install pytest pytest-cov pytest-mock` で依存関係をインストール

### gh CLI が利用できない
- 症状: "Not in PR context or gh CLI unavailable"
- 対処: 正常（PR情報は取得できないがRunログは生成される）

---

*最終更新: 2025-09-06 JST*
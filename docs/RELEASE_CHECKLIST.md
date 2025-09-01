# StrataRegula リリースチェックリスト

## 📋 リリース前チェックリスト

### 1. コード品質
- [ ] すべてのテストが通過している
  ```bash
  pytest tests/
  ```
- [ ] Lintエラーがない
  ```bash
  ruff check .
  ruff format --check .
  ```
- [ ] 型チェックが通過している
  ```bash
  mypy strataregula/
  ```
- [ ] セキュリティスキャンが完了
  ```bash
  bandit -r strataregula/
  ./secret-audit.ps1
  ```

### 2. バージョン管理
- [ ] `strataregula/__init__.py` のバージョン番号が正しい
- [ ] `pyproject.toml` の依存関係が最新
- [ ] `CHANGELOG.md` が更新されている
- [ ] タグ用のコミットメッセージが準備されている

### 3. ドキュメント
- [ ] README.md が最新の機能を反映している
- [ ] API ドキュメントが更新されている
- [ ] マイグレーションガイドが作成されている（破壊的変更がある場合）
- [ ] リリースノートが準備されている

### 4. CI/CD
- [ ] GitHub Actionsのすべてのワークフローが成功している
  - [ ] test.yml
  - [ ] quality-checks.yml
  - [ ] security.yml
  - [ ] golden-metrics.yml
  - [ ] benchmark.yml
- [ ] ブランチ保護ルールが適用されている

### 5. パフォーマンス
- [ ] ベンチマークが基準値を満たしている
  ```bash
  python benchmarks/perf_suite.py
  ```
- [ ] Golden Metrics Guardが通過している
  ```bash
  python scripts/golden_capture.py
  pytest tests/golden/test_regression_guard.py
  ```

## 🚀 リリース実行手順

### 1. 最終確認
```bash
# ブランチの確認
git branch
git status

# 最新の変更を取得
git pull origin master
```

### 2. テストの実行
```bash
# フルテストスイート実行
pytest tests/ -v --cov=strataregula

# ベンチマーク実行
python benchmarks/perf_suite.py --full
```

### 3. パッケージビルド
```bash
# クリーンビルド
rm -rf dist/ build/ *.egg-info/
python -m build

# ビルド内容の確認
twine check dist/*
```

### 4. タグの作成
```bash
# バージョンタグを作成（例: v0.3.0）
git tag -a v0.3.0 -m "Release v0.3.0: Kernel Architecture & Config Interning"
git push origin v0.3.0
```

### 5. PyPIへのアップロード
```bash
# TestPyPIで確認（オプション）
twine upload --repository testpypi dist/*

# 本番PyPIへアップロード
twine upload dist/*
```

### 6. GitHubリリースの作成
1. GitHub リポジトリの "Releases" ページへ移動
2. "Draft a new release" をクリック
3. タグを選択（v0.3.0）
4. リリースノートを記入
5. アセット（wheel, tar.gz）をアップロード
6. "Publish release" をクリック

## 📋 リリース後チェックリスト

### 1. 動作確認
- [ ] PyPIからインストールできることを確認
  ```bash
  pip install strataregula==0.3.0
  ```
- [ ] 基本的な機能が動作することを確認
  ```python
  from strataregula import Kernel
  kernel = Kernel()
  ```

### 2. ドキュメント更新
- [ ] リリースノートがGitHubに公開されている
- [ ] ドキュメントサイトが更新されている（該当する場合）
- [ ] 依存プロジェクトへの通知（world-simulation等）

### 3. 監視
- [ ] PyPIダウンロード数の監視
- [ ] Issue/バグレポートの監視（24-48時間）
- [ ] パフォーマンスメトリクスの確認

### 4. フォローアップ
- [ ] 次バージョンの開発ブランチを作成
- [ ] バックログの整理と優先順位付け
- [ ] リリース振り返りの実施

## 🔧 トラブルシューティング

### PyPIアップロードエラー
```bash
# 認証情報の確認
cat ~/.pypirc

# パッケージ名の重複確認
pip search strataregula
```

### タグの修正が必要な場合
```bash
# タグの削除（ローカル）
git tag -d v0.3.0

# タグの削除（リモート）
git push origin :refs/tags/v0.3.0

# 新しいタグを作成
git tag -a v0.3.0 -m "Updated release message"
git push origin v0.3.0
```

### ロールバックが必要な場合
```bash
# PyPIからバージョンを削除（削除は推奨されない）
# 代わりにパッチバージョンをリリース
python -m build
twine upload dist/*strataregula-0.3.1*
```

## 📝 メモ

- リリース作業は必ず master ブランチから実行する
- タグ作成前に必ず全テストを実行する
- PyPIへのアップロードは取り消しができないため慎重に行う
- セキュリティ関連の変更がある場合は SECURITY.md も更新する

---

最終更新: 2025-09-01
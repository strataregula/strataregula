# 環境トラブルシューティング 🔧

最短で原因切り分けできるよう、症状別→原因→対処の順でまとめます。  
まずは **Python 3.11 / venv 有効化 / `pip install -r requirements.txt` 完了**を前提にチェックしてください。

---

## 0. クイック診断（最初に実行）
```bash
python -V
which python || where python
python -c "import sys,platform;print(sys.version, platform.platform())"
python -m pip -V
pytest -q || true
ruff --version || true
```

---

## A. 依存関係系

### A-1. `pytest: command not found` / `ModuleNotFoundError`

**原因**: venv 未有効化 / 依存未インストール
**対処**
```bash
# venv 再作成〜有効化
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### A-2. `pip install` でビルド失敗

**原因**: 古い pip / キャッシュ破損
**対処**
```bash
pip install -U pip setuptools wheel
pip cache purge
pip install -r requirements.txt
```

---

## B. テスト・カバレッジ系

### B-1. `pytest --cov` が認識されない

**原因**: `pytest-cov` 未導入
**対処**
```bash
pip install pytest-cov
pytest --cov=src --cov-report=term-missing:skip-covered
```

### B-2. CI では通るがローカルでカバレッジ不足

**原因**: Python minor の違い / 無効テスト選別
**対処**
- ローカルを **Python 3.11** に合わせる（pyenv 推奨）
- `pytest.ini` / `conftest.py` のマーカー／除外設定を確認

---

### B-3. `pytest` でモジュールインポートエラー / __pycache__ 問題

**原因**: 古いキャッシュファイルの競合 / パス問題
**対処**
```bash
# キャッシュクリア
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# venv 再有効化してからテスト
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pytest -q
```

---

## C. Lint / Format 系

### C-1. `ruff check .` で大量エラー

**原因**: ルール未把握 / 旧フォーマット残り
**対処**
```bash
ruff check . --fix
# 併せて
black .
isort .
```

**基準**: リリース前は **ruff エラー 0**（詳細は RELEASE_CHECKLIST 参照）

---

## D. 文字化け・エンコーディング

### D-1. Windows で日本語が化ける / UnicodeError

**原因**: 既定コードページ
**対処（PowerShell/CMD）**
```cmd
chcp 65001
setx PYTHONUTF8 1
setx PYTHONIOENCODING UTF-8
```

---

## E. CLI / 実行時の既知事象

### E-1. `cli_plan` が `.cache/last_run_metrics.json` 無いと失敗

**対処**
```bash
python -m src.simroute_core.cli_run --prefectures configs/prefectures.yaml --resources configs/resources.yaml --routes configs/routes.yaml --traffic configs/traffic.yaml
python -m src.simroute_core.cli_plan --prefectures configs/prefectures.yaml --resources configs/resources.yaml --traffic configs/traffic.yaml --snapshot .cache/last_run_metrics.json --target 0.70
```

### E-2. ベンチマーク結果がブレる

**原因**: 省電力設定 / バックグラウンド負荷
**対処**
- 電源プランを高パフォーマンス
- 他の重いプロセス停止
- 計測は最低 3 回実施し平均を見る

---

## F. DevContainer / Docker

### F-1. `Reopen in Container` で失敗（proxy / ghcr.io 403）

**対処**
- Proxy 環境変数を VS Code + Docker に揃える
  `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`
- 企業プロキシ経由では `ghcr.io` ブロックの可能性 → 管理者に許可申請

### F-2. 権限/UID 問題でボリュームに書けない

**対処**
- `.devcontainer.json` の `remoteUser` / `containerUser` をホスト UID/GID に合わせる
- Linux ホストなら `id -u`, `id -g` を確認

---

## G. Git / Runログ

### G-1. どの変更がマージ済みか不明

**対処**
```bash
git fetch -p
git log --oneline --decorate --graph -20
git --no-pager diff --compact-summary origin/main...HEAD
```

### G-2. Runログの時刻が UTC になってしまう

**対処**: ログ生成スクリプト側のタイムゾーン指定（JST固定）を確認
（テンプレートは JST 表示ルール）

---

## H. 最終手段（環境リセット）

```bash
deactivate 2>/dev/null || true
rm -rf .venv .cache __pycache__
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

> これでも解決しない場合は、OS / Python 版 / `pip list` / エラーログを添えて Issue へ。
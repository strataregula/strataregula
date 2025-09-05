# 開発環境セットアップガイド 🛠️

新規参加者が 15 分で着手できることを目標とした手順です。

---

## 1) 前提条件
- **Python 3.11以上（推奨: 3.11、動作確認済み: 3.11〜3.13）**
- Git / GitHub
- OS：Linux / macOS / Windows（いずれも可）

> 既存ルール：Runログは常に作成（`CONTRIBUTING.md` 参照）

---

## 2) 仮想環境の作成
```bash
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows
# .venv\Scripts\activate
```

---

## 3) 依存関係の導入
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**オプション（必要に応じて）**
```bash
# 厳格モード（設定バリデーション）
pip install "pydantic>=2"

# SimPy ランタイム
pip install "simpy>=4"
```

---

## 4) 開発補助（推奨）
```bash
pip install pre-commit ruff black isort
pre-commit install
```

---

## 5) 動作確認
```bash
# ユニットテスト
pytest -q

# カバレッジ
pytest --cov=src --cov-report=term-missing:skip-covered

# デモ実行（例）
python -m src.simroute_core.cli_run \
  --prefectures configs/prefectures.yaml \
  --resources   configs/resources.yaml \
  --routes      configs/routes.yaml \
  --traffic     configs/traffic.yaml \
  --auto-compile
```

---

## 6) よくあるトラブルと対処

- **Windows の文字化け／Unicode エラー**
  ```cmd
  chcp 65001
  set PYTHONUTF8=1
  set PYTHONIOENCODING=UTF-8
  ```
- **キャッシュ破損時**：`.cache/` ディレクトリを削除して再実行
- **ベンチが不安定**：電源プランを高パフォーマンス、バックグラウンド負荷を停止

---

## 7) DevContainer（VS Code）

- VS Code + Dev Containers 拡張を利用
- `.devcontainer/` が存在する場合は「Reopen in Container」
- 共有の Docker 環境でセットアップを均一化

---

## 8) CI 環境との差異（概要）

- **ローカル**：自由な検証（Python minor が異なる場合あり）
- **CI**：Python 3.11 固定、`ruff` エラー 0、カバレッジ ≥ 90%、Golden Bench 合格が必須

---

## 9) 次ステップ

- Runログ作成：`docs/run/_TEMPLATE.md` をコピーして記録
- 変更は小さく・目的を一つに（`.development-rules.md`）
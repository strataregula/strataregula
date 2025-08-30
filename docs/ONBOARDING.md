# 新人向けオンボーディングガイド 🚀

新規参加者が迷わない入口を標準化します。以下の順序でご覧ください：

## 学習順序

1. **README.md** → 全体像とプロジェクト概要
2. **docs/README_FOR_DEVELOPERS.md** → 開発ルール/Runログ文化/テスト方法  
3. **CONTRIBUTING.md** → 1PR=1目的, RunログSummary非空
4. **AGENTS.md** → 自動化手順とRun Log Agentの使い方
5. **DevContainer** → VS Code "Reopen in Container" で統一環境

## Quick Start

```bash
# DevContainer推奨（統一環境）
# VS Code: "Reopen in Container"

# テスト実行
pytest -q
pytest --cov=src --cov-report=term-missing:skip-covered

# Run Log作成
python tools/runlog.py --label onboarding-test --summary "初回環境テスト" --intent "開発環境の動作確認"
```

## 重要な文化

- **1 PR = 1 目的**: 小さな変更に分割
- **Runログ必須**: docs/run/*.md にSummary非空・JST時刻で記録
- **CI グリーン**: マージ前に必ず品質チェック通過

## サポート

- GitHub Issues で質問
- AGENTS.md で自動化手順確認
- docs/run/ の過去ログを参照
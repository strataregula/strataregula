#!/usr/bin/env bash
set -euo pipefail

# VS Code自動ファイル表示（バックグラウンドで実行）
if [ -f docs/README_FOR_DEVELOPERS.md ]; then
  echo -e "
[devcontainer] 開発前に必ず docs/README_FOR_DEVELOPERS.md を確認してください。"
  
  # VS Code でファイルを開く（非ブロッキング）
  if command -v code >/dev/null 2>&1; then
    (sleep 2 && code docs/README_FOR_DEVELOPERS.md) &
  fi
fi

# プロジェクト情報表示
echo -e "
🚀 StrataRegula Core Framework Development Environment"
echo "📝 Quick Commands:"
echo "  - pytest -q                           # Run tests"
echo "  - pytest --cov=src --cov-report=term-missing:skip-covered # Coverage"
echo "  - ruff check . && ruff format          # Code quality"
echo "  - python -m strataregula.cli --help    # CLI help"
echo "  - python scripts/bench_guard.py        # Benchmarks"
echo ""

# --- Auto-open AGENTS.md for read-and-follow culture ---
if [ -f "AGENTS.md" ]; then
  code -r AGENTS.md >/dev/null 2>&1 || true
fi
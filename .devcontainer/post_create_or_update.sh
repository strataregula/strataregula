#!/usr/bin/env bash
set -euo pipefail

if [ -f docs/README_FOR_DEVELOPERS.md ]; then
  echo "==============================================="
  echo " 開発前に必ず読む資料 (docs/README_FOR_DEVELOPERS.md)"
  echo "==============================================="
  sed -n '1,120p' docs/README_FOR_DEVELOPERS.md || true
  echo -e "\n(全文は docs/README_FOR_DEVELOPERS.md を参照)"
fi

# Python 依存（任意）
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
if [ -f pyproject.toml ]; then
  uv sync || true
fi

# Node 依存（VSCode拡張など）
if [ -f package.json ]; then
  corepack enable || true
  if command -v pnpm >/dev/null 2>&1; then
    pnpm install || true
  else
    npm ci || npm install || true
  fi
fi

# pre-commit（プロキシ環境では失敗しても継続）
if [ -f .pre-commit-config.yaml ]; then
  pip install pre-commit || true
  pre-commit install || true
fi

echo "[setup] done."
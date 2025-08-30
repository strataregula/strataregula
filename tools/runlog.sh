#!/usr/bin/env bash
set -euo pipefail
label="${1:-manual}"
summary="${2:-"no summary"}"
intent="${3:-"no intent"}"

ts=$(TZ=Asia/Tokyo date +"%Y-%m-%dT%H-%MJST")
repo=$(basename "$(pwd)")
mkdir -p docs/run
f="docs/run/${ts}-${label}.md"
cat > "$f" <<EOL
# Run Log - ${label}
- When: ${ts}
- Repo: ${repo}
- Summary: ${summary}

## Intent
${intent}

## Commands
(ここに実行コマンドを列挙)

## Results
(結果の要点を記述)

## Next actions
- 追加対応を記述
EOL
echo "$f"

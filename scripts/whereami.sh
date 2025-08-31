#!/usr/bin/env bash
set -e

root=$(git rev-parse --show-toplevel 2>/dev/null || echo "?")
repo=$(basename "$root")
remote=$(git remote get-url origin 2>/dev/null || echo "no-remote")
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
host=$(printf '%s\n' "$remote" | sed -E 's#^[^@]+@([^:/]+).*#\1#; t; s#^https?://([^/]+)/.*#\1#')

echo "📦 $repo  🌿 $branch  🔗 $remote  🏷 host=$host  ✉ $(git config user.email 2>/dev/null)"
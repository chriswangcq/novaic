#!/usr/bin/env bash
# 按 docs/ 下第一级目录统计 .md 篇数，便于 PR 中对照 DOCUMENT_INVENTORY 或策略门禁。
# 用法：在仓库根目录执行 ./scripts/docs-count.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
total=$(find docs -name '*.md' | wc -l | tr -d ' ')
echo "docs/**/*.md 合计: ${total}"
echo ""
echo "按第一级目录:"
find docs -name '*.md' -print \
  | sed 's|^docs/||' \
  | awk -F/ '{ if (NF==1) print "(根目录)"; else print $1 }' \
  | sort \
  | uniq -c \
  | sort -nr

#!/usr/bin/env bash
# Generate docs/_archive/MANIFEST-<suffix>.txt — list of all docs/**/*.md at snapshot time.
# Usage (from repo root): bash docs/_scripts/snapshot_docs_manifest.sh [suffix]
# Example: bash docs/_scripts/snapshot_docs_manifest.sh 2026-04-09-pre-rebuild
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
SUFFIX="${1:-$(date +%Y-%m-%d)}"
OUT="docs/_archive/MANIFEST-${SUFFIX}.txt"
mkdir -p docs/_archive
find docs -name '*.md' -type f | sed 's|^\./||' | sort >"$OUT"
echo "Wrote $OUT ($(wc -l <"$OUT" | tr -d ' ') paths)"

#!/usr/bin/env bash
# Guard active source and packaged resource trees from generated Python/test
# cache artifacts. These files are ignored by git, but they still mislead
# source scans and can leak into packaged App resources.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

matches="$(
  find . \
    \( \
      -path './.git' -o -path './*/.git' -o \
      -path './node_modules' -o -path './*/node_modules' -o \
      -path './target' -o -path './*/target' -o \
      -path './.venv' -o -path './*/.venv' -o \
      -path './thirdparty' -o -path './*/target' -o \
      -path './novaic-app/src-tauri/gen/apple/build' \
    \) -prune -o \
    \( \
      -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.egg-info' \) -o \
      -type f -name '*.pyc' \
    \) -print
)"

if [[ -n "$matches" ]]; then
  echo "[generated-artifacts] active source/resource generated artifacts found:" >&2
  echo "$matches" >&2
  exit 1
fi

echo "GENERATED_ARTIFACTS_LINT=PASS"

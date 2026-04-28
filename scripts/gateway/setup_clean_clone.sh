#!/usr/bin/env bash
# setup_clean_clone.sh — clone all dependencies and run smoke test.
#
# Run this from inside a clean clone of novaic-gateway:
#   git clone https://github.com/chriswangcq/novaic-gateway
#   cd novaic-gateway
#   bash scripts/setup_clean_clone.sh
#
# The script clones required sibling repos next to this repo and then
# runs scripts/smoke_gateway_repo_root.sh.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_DIR="$(cd "$REPO_ROOT/.." && pwd)"

RUNTIME_REPO_URL="${RUNTIME_REPO_URL:-https://github.com/chriswangcq/novaic-runtime-orchestrator}"
SHARED_COMMON_URL="${SHARED_COMMON_URL:-https://github.com/chriswangcq/novaic}"

RUNTIME_DIR="${RUNTIME_REPO_DIR:-$PARENT_DIR/novaic-runtime-orchestrator}"
SHARED_DIR="${NOVAIC_SHARED_COMMON_PATH:-$PARENT_DIR/novaic-shared-runtime-common}"

clone_if_missing() {
  local url="$1" dest="$2"
  if [ ! -d "$dest/.git" ]; then
    echo "[setup_clean_clone] cloning $url -> $dest"
    git clone "$url" "$dest"
  else
    echo "[setup_clean_clone] already present: $dest"
  fi
}

clone_if_missing "$RUNTIME_REPO_URL" "$RUNTIME_DIR"
clone_if_missing "$SHARED_COMMON_URL" "$SHARED_DIR"

echo "[setup_clean_clone] running smoke test..."
RUNTIME_REPO_DIR="$RUNTIME_DIR" \
NOVAIC_SHARED_COMMON_PATH="$SHARED_DIR" \
bash "$REPO_ROOT/scripts/smoke_gateway_repo_root.sh"

echo "SETUP_CLEAN_CLONE_COMPLETE=PASS"

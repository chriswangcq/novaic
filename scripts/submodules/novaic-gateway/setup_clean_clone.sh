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

TOOLS_REPO_URL="${TOOLS_REPO_URL:-https://github.com/chriswangcq/novaic-tools-server}"

TOOLS_DIR="${TOOLS_REPO_DIR:-$PARENT_DIR/novaic-tools-server}"

clone_if_missing() {
  local url="$1" dest="$2"
  if [ ! -d "$dest/.git" ]; then
    echo "[setup_clean_clone] cloning $url -> $dest"
    git clone "$url" "$dest"
  else
    echo "[setup_clean_clone] already present: $dest"
  fi
}

clone_if_missing "$TOOLS_REPO_URL" "$TOOLS_DIR"

echo "[setup_clean_clone] running smoke test..."
TOOLS_REPO_DIR="$TOOLS_DIR" \
bash "$REPO_ROOT/scripts/smoke_gateway_repo_root.sh"

echo "SETUP_CLEAN_CLONE_COMPLETE=PASS"

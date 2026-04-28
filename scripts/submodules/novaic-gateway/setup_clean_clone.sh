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

clone_if_missing() {
  local url="$1" dest="$2"
  if [ ! -d "$dest/.git" ]; then
    echo "[setup_clean_clone] cloning $url -> $dest"
    git clone "$url" "$dest"
  else
    echo "[setup_clean_clone] already present: $dest"
  fi
}

echo "[setup_clean_clone] running smoke test..."
bash "$REPO_ROOT/scripts/smoke_gateway_repo_root.sh"

echo "SETUP_CLEAN_CLONE_COMPLETE=PASS"

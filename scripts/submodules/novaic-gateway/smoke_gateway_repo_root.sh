#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Sibling-repo paths are configurable via env vars for clean-clone workflow.
# Set GATEWAY_ONLY_SMOKE=1 to skip starting sibling services and test gateway only.
GATEWAY_ONLY_SMOKE="${GATEWAY_ONLY_SMOKE:-0}"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BOOTSTRAP_BIN="${PYTHON_BOOTSTRAP_BIN:-python3}"

resolve_python_bin() {
  # Always use the split repo's local .venv — no external PYTHON_BIN override accepted.
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$PYTHON_BOOTSTRAP_BIN" -m venv "$VENV_DIR"
  fi
  if ! "$VENV_DIR/bin/python" -c "import uvicorn, fastapi, httpx" >/dev/null 2>&1; then
    "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
    "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/requirements.txt" >/dev/null
  fi
  echo "$VENV_DIR/bin/python"
}

PYTHON_BIN="$(resolve_python_bin)"

GW_PID=""

cleanup() {
  set +e
  if [ -n "$GW_PID" ]; then
    kill "$GW_PID" >/dev/null 2>&1 || true
    wait "$GW_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_http() {
  local url="$1"
  local retries="${2:-80}"
  for _ in $(seq 1 "$retries"); do
    if curl --noproxy '*' -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

if [ "$GATEWAY_ONLY_SMOKE" = "1" ]; then
  cd "$ROOT_DIR"
  GATEWAY_HOST="127.0.0.1" \
  GATEWAY_PORT="20000" \
  "$PYTHON_BIN" services/gateway_api.py > /tmp/novaic-gateway-split.log 2>&1 &
  GW_PID="$!"
  if ! wait_for_http "http://127.0.0.1:19999/api/health"; then
    echo "ERROR: gateway health check failed (standalone mode)"
    exit 1
  fi
  echo "GATEWAY_DECOUPLED_FROM_SPLIT_SERVICES=PASS"
  echo "SPLIT_GATEWAY_HEALTH=PASS"
  echo "CLEAN_CLONE_WORKFLOW_READY=PASS"
else
  cd "$ROOT_DIR"
  GATEWAY_HOST="127.0.0.1" \
  GATEWAY_PORT="20000" \
  "$PYTHON_BIN" services/gateway_api.py > /tmp/novaic-gateway-split.log 2>&1 &
  GW_PID="$!"

  if ! wait_for_http "http://127.0.0.1:19999/api/health"; then
    echo "ERROR: gateway health check failed"
    exit 1
  fi

  curl --noproxy '*' -fsS "http://127.0.0.1:19999/api/system/status" >/dev/null
  "$ROOT_DIR/scripts/replay_gateway_runtime_chain.sh"

  echo "SPLIT_GATEWAY_HEALTH=PASS"
  echo "SPLIT_GATEWAY_STATUS_ROUTE=PASS"
  echo "CLEAN_CLONE_WORKFLOW_READY=PASS"
fi

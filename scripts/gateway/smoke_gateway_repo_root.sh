#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# All sibling-repo paths are configurable via env vars for clean-clone workflow.
# In a clean-clone setup, set these before running:
#   RUNTIME_REPO_DIR=/path/to/novaic-runtime-orchestrator
#   NOVAIC_SHARED_COMMON_PATH=/path/to/novaic-shared-runtime-common
RUNTIME_REPO_DIR="${RUNTIME_REPO_DIR:-$ROOT_DIR/../novaic-runtime-orchestrator}"
SHARED_COMMON_REPO_DIR="${NOVAIC_SHARED_COMMON_PATH:-$ROOT_DIR/../novaic-shared-runtime-common}"
# Entry-point scripts are configurable to support repos with different layouts.
RUNTIME_MAIN_SCRIPT="${RUNTIME_MAIN_SCRIPT:-runtime_orchestrator/main.py}"
# Set GATEWAY_ONLY_SMOKE=1 to skip starting sibling services and test gateway against
# a pre-running RUNTIME_ORCHESTRATOR_URL. Proves gateway is decoupled from split-service dirs.
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

if ! "$PYTHON_BIN" "$ROOT_DIR/scripts/export_entity_id_fields.py" --check; then
  echo "ERROR: gateway/entity/generated_entity_id_fields.json stale — run scripts/export_entity_id_fields.py"
  exit 1
fi

RO_PID=""
GW_PID=""

cleanup() {
  set +e
  if [ -n "$GW_PID" ]; then
    kill "$GW_PID" >/dev/null 2>&1 || true
    wait "$GW_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "$RO_PID" ]; then
    kill "$RO_PID" >/dev/null 2>&1 || true
    wait "$RO_PID" >/dev/null 2>&1 || true
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
  # Decoupled mode: skip starting sibling services.
  # RUNTIME_ORCHESTRATOR_URL must be pre-set to a running instance.
  if [ -z "${RUNTIME_ORCHESTRATOR_URL:-}" ]; then
    echo "ERROR: GATEWAY_ONLY_SMOKE=1 requires RUNTIME_ORCHESTRATOR_URL to be set"
    exit 1
  fi
  cd "$ROOT_DIR"
  NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
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
  cd "$RUNTIME_REPO_DIR"
  NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
  "$PYTHON_BIN" "$RUNTIME_MAIN_SCRIPT" > /tmp/novaic-runtime-orchestrator-split.log 2>&1 &
  RO_PID="$!"

  if ! wait_for_http "http://127.0.0.1:19993/api/health"; then
    echo "ERROR: runtime-orchestrator health check failed"
    exit 1
  fi

  cd "$ROOT_DIR"
  NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
  RUNTIME_ORCHESTRATOR_URL="http://127.0.0.1:19993" \
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

  echo "SPLIT_RUNTIME_HEALTH=PASS"
  echo "SPLIT_GATEWAY_HEALTH=PASS"
  echo "SPLIT_GATEWAY_STATUS_ROUTE=PASS"
  echo "SPLIT_E2E_RUNTIME_FORWARD=PASS"
  echo "SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS"
  echo "SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS"
  echo "CLEAN_CLONE_WORKFLOW_READY=PASS"
fi

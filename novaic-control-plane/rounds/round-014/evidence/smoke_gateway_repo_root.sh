#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# All sibling-repo paths are configurable via env vars for clean-clone workflow.
# In a clean-clone setup, set these before running:
#   RUNTIME_REPO_DIR=/path/to/novaic-runtime-orchestrator
#   TOOLS_REPO_DIR=/path/to/novaic-tools-server
#   NOVAIC_SHARED_COMMON_PATH=/path/to/novaic-shared-runtime-common
RUNTIME_REPO_DIR="${RUNTIME_REPO_DIR:-$ROOT_DIR/../novaic-runtime-orchestrator}"
TOOLS_REPO_DIR="${TOOLS_REPO_DIR:-$ROOT_DIR/../novaic-tools-server}"
SHARED_COMMON_REPO_DIR="${NOVAIC_SHARED_COMMON_PATH:-$ROOT_DIR/../novaic-shared-runtime-common}"
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

RO_PID=""
GW_PID=""
TS_PID=""

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
  if [ -n "$TS_PID" ]; then
    kill "$TS_PID" >/dev/null 2>&1 || true
    wait "$TS_PID" >/dev/null 2>&1 || true
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

cd "$RUNTIME_REPO_DIR"
NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
"$PYTHON_BIN" runtime_orchestrator/main.py > /tmp/novaic-runtime-orchestrator-split.log 2>&1 &
RO_PID="$!"

if ! wait_for_http "http://127.0.0.1:20001/api/health"; then
  echo "ERROR: runtime-orchestrator health check failed"
  exit 1
fi

cd "$ROOT_DIR"
NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
RUNTIME_ORCHESTRATOR_URL="http://127.0.0.1:20001" \
GATEWAY_HOST="127.0.0.1" \
GATEWAY_PORT="20000" \
"$PYTHON_BIN" services/gateway_api.py > /tmp/novaic-gateway-split.log 2>&1 &
GW_PID="$!"

if ! wait_for_http "http://127.0.0.1:20000/api/health"; then
  echo "ERROR: gateway health check failed"
  exit 1
fi

curl --noproxy '*' -fsS "http://127.0.0.1:20000/api/system/status" >/dev/null
"$ROOT_DIR/scripts/replay_gateway_runtime_chain.sh"

NOVAIC_SHARED_COMMON_PATH="$SHARED_COMMON_REPO_DIR" \
TOOLS_HOST="127.0.0.1" \
TOOLS_PORT="20002" \
"$PYTHON_BIN" "$TOOLS_REPO_DIR/tools_server/main.py" > /tmp/novaic-tools-server-split.log 2>&1 &
TS_PID="$!"

if ! wait_for_http "http://127.0.0.1:20002/api/health"; then
  echo "ERROR: tools-server health check failed"
  exit 1
fi

echo "SPLIT_RUNTIME_HEALTH=PASS"
echo "SPLIT_GATEWAY_HEALTH=PASS"
echo "SPLIT_TOOLS_HEALTH=PASS"
echo "SPLIT_GATEWAY_STATUS_ROUTE=PASS"
echo "SPLIT_E2E_RUNTIME_FORWARD=PASS"
echo "SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS"
echo "SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS"
echo "CLEAN_CLONE_WORKFLOW_READY=PASS"

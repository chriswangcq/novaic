#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SPLIT_REPOS_ROOT="$REPO_ROOT/rounds/round-003/split-move/repos"
GATEWAY_REPO="$SPLIT_REPOS_ROOT/novaic-gateway"
RUNTIME_REPO="$SPLIT_REPOS_ROOT/novaic-runtime-orchestrator"
TOOLS_REPO="$SPLIT_REPOS_ROOT/novaic-tools-server"
SHARED_REPO="$SPLIT_REPOS_ROOT/novaic-shared-runtime-common"
MONOREPO_PYTHON_FALLBACK="$REPO_ROOT/../novaic-backend/venv/bin/python3"

resolve_python_bin() {
  if [ -n "${PYTHON_BIN:-}" ] && "$PYTHON_BIN" -c "import uvicorn, fastapi, httpx" >/dev/null 2>&1; then
    echo "$PYTHON_BIN"
    return
  fi
  if command -v python3 >/dev/null 2>&1 && python3 -c "import uvicorn, fastapi, httpx" >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if [ -x "$MONOREPO_PYTHON_FALLBACK" ] && "$MONOREPO_PYTHON_FALLBACK" -c "import uvicorn, fastapi, httpx" >/dev/null 2>&1; then
    echo "$MONOREPO_PYTHON_FALLBACK"
    return
  fi
  echo "python3"
}

PYTHON_BIN="$(resolve_python_bin)"

RO_PID=""
GW_PID=""
TS_PID=""

cleanup() {
  set +e
  [ -n "$GW_PID" ] && kill "$GW_PID" >/dev/null 2>&1 || true
  [ -n "$RO_PID" ] && kill "$RO_PID" >/dev/null 2>&1 || true
  [ -n "$TS_PID" ] && kill "$TS_PID" >/dev/null 2>&1 || true
  [ -n "$GW_PID" ] && wait "$GW_PID" >/dev/null 2>&1 || true
  [ -n "$RO_PID" ] && wait "$RO_PID" >/dev/null 2>&1 || true
  [ -n "$TS_PID" ] && wait "$TS_PID" >/dev/null 2>&1 || true
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

cd "$RUNTIME_REPO"
NOVAIC_SHARED_COMMON_PATH="$SHARED_REPO" \
"$PYTHON_BIN" runtime_orchestrator/main.py > /tmp/novaic-r004-runtime.log 2>&1 &
RO_PID="$!"
wait_for_http "http://127.0.0.1:20001/api/health"

cd "$TOOLS_REPO"
NOVAIC_SHARED_COMMON_PATH="$SHARED_REPO" \
TOOLS_HOST="127.0.0.1" TOOLS_PORT="20002" \
"$PYTHON_BIN" tools_server/main.py > /tmp/novaic-r004-tools.log 2>&1 &
TS_PID="$!"
wait_for_http "http://127.0.0.1:20002/api/health"

cd "$GATEWAY_REPO"
NOVAIC_SHARED_COMMON_PATH="$SHARED_REPO" \
RUNTIME_ORCHESTRATOR_URL="http://127.0.0.1:20001" \
GATEWAY_HOST="127.0.0.1" GATEWAY_PORT="20000" \
"$PYTHON_BIN" services/gateway_api.py > /tmp/novaic-r004-gateway.log 2>&1 &
GW_PID="$!"
wait_for_http "http://127.0.0.1:20000/api/health"

curl --noproxy '*' -fsS "http://127.0.0.1:20000/api/runtime-orchestrator/health" >/dev/null
curl --noproxy '*' -fsS "http://127.0.0.1:20002/api/health" >/dev/null

echo "ROUND004_MULTI_REPO_BRINGUP_PASS"

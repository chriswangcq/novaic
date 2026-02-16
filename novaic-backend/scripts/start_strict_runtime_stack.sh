#!/usr/bin/env bash
set -euo pipefail

# Strict startup: Runtime Orchestrator -> Gateway
# Usage:
#   bash scripts/start_strict_runtime_stack.sh [DATA_DIR] [RO_PORT] [GW_PORT]

DATA_DIR="${1:-${NOVAIC_DATA_DIR:-}}"
RO_PORT="${2:-19993}"
GW_PORT="${3:-19999}"
RO_HOST="127.0.0.1"

if [[ -z "${DATA_DIR}" ]]; then
  echo "[strict-start] ERROR: data dir is required"
  echo "[strict-start] Usage: bash scripts/start_strict_runtime_stack.sh /path/to/data [RO_PORT] [GW_PORT]"
  exit 1
fi

mkdir -p "${DATA_DIR}/logs"

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="localhost,127.0.0.1,::1"
export NOVAIC_DATA_DIR="${DATA_DIR}"
export RUNTIME_ORCHESTRATOR_HOST="${RO_HOST}"
export RUNTIME_ORCHESTRATOR_PORT="${RO_PORT}"
export RUNTIME_ORCHESTRATOR_URL="http://${RO_HOST}:${RO_PORT}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD="${PYTHON_BIN}"
elif [[ -x "${ROOT_DIR}/venv/bin/python" ]]; then
  PYTHON_CMD="${ROOT_DIR}/venv/bin/python"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_CMD="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_CMD="python3"
fi

RO_LOG="${DATA_DIR}/logs/runtime-orchestrator.log"
GW_LOG="${DATA_DIR}/logs/gateway.log"
RO_PID_FILE="${DATA_DIR}/runtime-orchestrator.pid"
GW_PID_FILE="${DATA_DIR}/gateway.pid"

echo "[strict-start] Starting Runtime Orchestrator on ${RO_HOST}:${RO_PORT}"
NOVAIC_DB_FILE="runtime_orchestrator.db" "${PYTHON_CMD}" "${ROOT_DIR}/main_novaic.py" runtime-orchestrator \
  --port "${RO_PORT}" \
  --host "${RO_HOST}" \
  --data-dir "${DATA_DIR}" >"${RO_LOG}" 2>&1 &
RO_PID=$!
echo "${RO_PID}" > "${RO_PID_FILE}"

echo "[strict-start] Waiting Runtime Orchestrator health..."
RO_HEALTH_URL="http://${RO_HOST}:${RO_PORT}/api/health"
for _ in $(seq 1 40); do
  if curl -sSf "${RO_HEALTH_URL}" >/dev/null 2>&1; then
    echo "[strict-start] Runtime Orchestrator is healthy"
    break
  fi
  sleep 0.5
done

if ! curl -sSf "${RO_HEALTH_URL}" >/dev/null 2>&1; then
  echo "[strict-start] ERROR: Runtime Orchestrator failed health check"
  if kill -0 "${RO_PID}" 2>/dev/null; then
    kill "${RO_PID}" 2>/dev/null || true
  fi
  rm -f "${RO_PID_FILE}"
  echo "[strict-start] Runtime Orchestrator log: ${RO_LOG}"
  exit 1
fi

echo "[strict-start] Starting Gateway on 127.0.0.1:${GW_PORT}"
NOVAIC_DB_FILE="gateway.db" "${PYTHON_CMD}" "${ROOT_DIR}/main_novaic.py" gateway \
  --port "${GW_PORT}" \
  --data-dir "${DATA_DIR}" >"${GW_LOG}" 2>&1 &
GW_PID=$!
echo "${GW_PID}" > "${GW_PID_FILE}"

echo "[strict-start] Waiting Gateway health..."
GW_HEALTH_URL="http://127.0.0.1:${GW_PORT}/api/health"
for _ in $(seq 1 40); do
  if curl -sSf "${GW_HEALTH_URL}" >/dev/null 2>&1; then
    echo "[strict-start] Gateway is healthy"
    break
  fi
  sleep 0.5
done

if ! curl -sSf "${GW_HEALTH_URL}" >/dev/null 2>&1; then
  echo "[strict-start] ERROR: Gateway failed health check"
  if kill -0 "${GW_PID}" 2>/dev/null; then
    kill "${GW_PID}" 2>/dev/null || true
  fi
  if kill -0 "${RO_PID}" 2>/dev/null; then
    kill "${RO_PID}" 2>/dev/null || true
  fi
  rm -f "${GW_PID_FILE}" "${RO_PID_FILE}"
  echo "[strict-start] Gateway log: ${GW_LOG}"
  exit 1
fi

echo "[strict-start] OK"
echo "[strict-start] Runtime Orchestrator PID: ${RO_PID} (${RO_PID_FILE})"
echo "[strict-start] Gateway PID: ${GW_PID} (${GW_PID_FILE})"
echo "[strict-start] Logs:"
echo "  - ${RO_LOG}"
echo "  - ${GW_LOG}"
echo "[strict-start] Python: ${PYTHON_CMD}"

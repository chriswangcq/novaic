#!/usr/bin/env bash
set -euo pipefail

# Strict stack stop: Gateway + Runtime Orchestrator
# Usage:
#   bash scripts/stop_strict_runtime_stack.sh [DATA_DIR]

DATA_DIR="${1:-${NOVAIC_DATA_DIR:-}}"

if [[ -z "${DATA_DIR}" ]]; then
  echo "[strict-stop] ERROR: data dir is required"
  echo "[strict-stop] Usage: bash scripts/stop_strict_runtime_stack.sh /path/to/data"
  exit 1
fi

GW_PID_FILE="${DATA_DIR}/gateway.pid"
RO_PID_FILE="${DATA_DIR}/runtime-orchestrator.pid"

stop_pid_file() {
  local pid_file="$1"
  local name="$2"

  if [[ ! -f "${pid_file}" ]]; then
    echo "[strict-stop] ${name}: pid file not found (${pid_file}), skip"
    return 0
  fi

  local pid
  pid="$(cat "${pid_file}" 2>/dev/null || true)"
  if [[ -z "${pid}" ]]; then
    echo "[strict-stop] ${name}: empty pid file (${pid_file}), removing"
    rm -f "${pid_file}"
    return 0
  fi

  if ! kill -0 "${pid}" 2>/dev/null; then
    echo "[strict-stop] ${name}: process ${pid} already stopped"
    rm -f "${pid_file}"
    return 0
  fi

  echo "[strict-stop] Stopping ${name} PID ${pid}"
  kill "${pid}" 2>/dev/null || true

  for _ in $(seq 1 20); do
    if ! kill -0 "${pid}" 2>/dev/null; then
      break
    fi
    sleep 0.2
  done

  if kill -0 "${pid}" 2>/dev/null; then
    echo "[strict-stop] ${name}: force killing PID ${pid}"
    kill -9 "${pid}" 2>/dev/null || true
  fi

  rm -f "${pid_file}"
  echo "[strict-stop] ${name}: stopped"
}

# Stop Gateway first, then Runtime Orchestrator.
stop_pid_file "${GW_PID_FILE}" "Gateway"
stop_pid_file "${RO_PID_FILE}" "Runtime Orchestrator"

echo "[strict-stop] OK"

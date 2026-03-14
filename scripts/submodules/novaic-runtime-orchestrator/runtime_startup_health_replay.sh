#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

PORT=19993
URL="http://127.0.0.1:${PORT}/api/health"
LOG_FILE="/tmp/novaic-runtime-orchestrator-startup.log"
PID=""

cleanup() {
  set +e
  if [ -n "$PID" ]; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python main_runtime_orchestrator.py runtime-orchestrator >"$LOG_FILE" 2>&1 &
PID="$!"

for _ in $(seq 1 120); do
  if curl --noproxy '*' -fsS "$URL" >/dev/null 2>&1; then
    echo "PASS: runtime-orchestrator startup from split repo root"
    echo "PASS: runtime health endpoint ${URL}"
    exit 0
  fi
  sleep 0.25
done

echo "FAIL: runtime-orchestrator health not reachable at ${URL}" >&2
echo "See log: ${LOG_FILE}" >&2
exit 1

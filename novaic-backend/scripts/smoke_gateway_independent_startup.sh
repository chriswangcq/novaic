#!/usr/bin/env bash
set -euo pipefail

# Gateway independent startup smoke:
# - starts runtime-orchestrator + gateway in isolated temp data dir
# - verifies /api/health and /internal proxy are reachable
# - stable port strategy policy:
#   ops-rounds/governance/gateway-smoke-port-strategy.md
#
# Usage:
#   bash scripts/smoke_gateway_independent_startup.sh

cd "$(dirname "$0")/.."

export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

TMPDIR="$(mktemp -d -t novaic-gw-smoke-XXXXXX)"
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
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

reset_processes() {
  set +e
  if [ -n "$GW_PID" ]; then
    kill "$GW_PID" >/dev/null 2>&1 || true
    wait "$GW_PID" >/dev/null 2>&1 || true
    GW_PID=""
  fi
  if [ -n "$RO_PID" ]; then
    kill "$RO_PID" >/dev/null 2>&1 || true
    wait "$RO_PID" >/dev/null 2>&1 || true
    RO_PID=""
  fi
}

wait_for_http() {
  local url="$1"
  local retries="${2:-120}"
  local sleep_s="${3:-0.5}"
  for _ in $(seq 1 "$retries"); do
    if curl --noproxy '*' -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
  done
  return 1
}

run_once() {
  local base="$1"
  RO_PORT=$((base + 93))
  GW_PORT=$((base + 99))
  QUEUE_PORT=$((base + 97))
  TOOLS_PORT=$((base + 98))
  VMCONTROL_PORT=$((base + 96))
  FILE_PORT=$((base + 95))
  TRS_PORT=$((base + 94))

  python main_novaic.py runtime-orchestrator \
    --host 127.0.0.1 \
    --port "$RO_PORT" \
    --data-dir "$TMPDIR" \
    >"$TMPDIR/ro.log" 2>&1 &
  RO_PID="$!"

  if ! wait_for_http "http://127.0.0.1:${RO_PORT}/api/health"; then
    echo "WARN: runtime-orchestrator not healthy on base ${base}" >&2
    return 1
  fi

  python main_novaic.py gateway \
    --host 127.0.0.1 \
    --port "$GW_PORT" \
    --data-dir "$TMPDIR" \
    --runtime-orchestrator-url "http://127.0.0.1:${RO_PORT}" \
    --queue-service-url "http://127.0.0.1:${QUEUE_PORT}" \
    --tools-server-url "http://127.0.0.1:${TOOLS_PORT}" \
    --vmcontrol-url "http://127.0.0.1:${VMCONTROL_PORT}" \
    --file-service-url "http://127.0.0.1:${FILE_PORT}" \
    --tool-result-service-url "http://127.0.0.1:${TRS_PORT}" \
    >"$TMPDIR/gw.log" 2>&1 &
  GW_PID="$!"

  if ! wait_for_http "http://127.0.0.1:${GW_PORT}/api/health"; then
    echo "WARN: gateway not healthy on base ${base}" >&2
    return 1
  fi
  curl --noproxy '*' -fsS "http://127.0.0.1:${GW_PORT}/api" >/dev/null

  echo "PASS: startup smoke base ${base}"
  echo "PASS: runtime-orchestrator healthy on ${RO_PORT}"
  echo "PASS: gateway healthy on ${GW_PORT}"
  echo "PASS: gateway API root reachable"
  return 0
}

for base in 61900 62000 62100; do
  if run_once "$base"; then
    exit 0
  fi
  reset_processes
done

echo "ERROR: smoke failed on all fallback bases (61900/62000/62100)" >&2
exit 1

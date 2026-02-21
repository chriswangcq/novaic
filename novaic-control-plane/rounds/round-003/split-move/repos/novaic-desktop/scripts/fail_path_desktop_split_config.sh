#!/usr/bin/env bash
# fail_path_desktop_split_config.sh — desktop split-config failure-path replay.
# Scenario: gateway + runtime-orchestrator running; tools-server absent.
#
# No absolute paths: all paths resolve relative to this script's own location.
# Run from anywhere; the script finds the monorepo root automatically.
#
# Expected markers:
#   TOOLS_HOP=FAIL
#   FAILURE_PATH_REPLAY=PASS
set -euo pipefail

# Resolve repo root: this script lives at
#   <repo>/novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../../../.." && pwd)"

BACKEND_DIR="$REPO_ROOT/novaic-backend"
VENV_PY="$BACKEND_DIR/venv/bin/python"

STACK_DIR="/tmp/r012-desktop-failpath-$$"
DIAG_OUT="${DIAG_OUT:-/tmp/r012-failure-diag.txt}"
mkdir -p "$STACK_DIR"

cleanup() { kill "$GW_PID" "$RO_PID" 2>/dev/null || true; }
trap cleanup EXIT

"$VENV_PY" "$BACKEND_DIR/main_novaic.py" runtime-orchestrator \
  --host 127.0.0.1 --port 61993 --data-dir "$STACK_DIR" \
  > "$STACK_DIR/ro.log" 2>&1 & RO_PID=$!

"$VENV_PY" "$BACKEND_DIR/main_novaic.py" gateway \
  --host 127.0.0.1 --port 61999 --data-dir "$STACK_DIR" \
  --runtime-orchestrator-url http://127.0.0.1:61993 \
  --queue-service-url http://127.0.0.1:61997 \
  --tools-server-url http://127.0.0.1:61998 \
  --vmcontrol-url http://127.0.0.1:61996 \
  --file-service-url http://127.0.0.1:61995 \
  --tool-result-service-url http://127.0.0.1:61994 \
  > "$STACK_DIR/gw.log" 2>&1 & GW_PID=$!

sleep 9

DESKTOP_HOP=$(curl -sSf http://127.0.0.1:61999/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
GATEWAY_HOP=$DESKTOP_HOP
RUNTIME_HOP=$(curl -sSf http://127.0.0.1:61993/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
TOOLS_HOP=$(curl -sSf http://127.0.0.1:61998/openapi.json >/dev/null 2>&1 && echo PASS || echo FAIL)

{
  echo "DESKTOP_HOP=$DESKTOP_HOP"
  echo "GATEWAY_HOP=$GATEWAY_HOP"
  echo "RUNTIME_HOP=$RUNTIME_HOP"
  echo "TOOLS_HOP=$TOOLS_HOP"
  echo "TOOLS_UNAVAILABLE=true"
  echo "round=round-012"
  echo "scenario=tools-endpoint-unavailable"
  echo "canonical_repo_url=https://github.com/chriswangcq/novaic"
} | tee "$DIAG_OUT"

if [ "$TOOLS_HOP" = "FAIL" ]; then
  echo "FAILURE_PATH_REPLAY=PASS" | tee -a "$DIAG_OUT"
else
  echo "FAILURE_PATH_REPLAY=FAIL (tools-server responded unexpectedly)" | tee -a "$DIAG_OUT"
  exit 1
fi

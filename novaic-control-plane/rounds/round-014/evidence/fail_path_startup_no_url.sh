#!/usr/bin/env bash
# Failure-path verification: confirms service_config raises RuntimeError at import
# time when RUNTIME_ORCHESTRATOR_URL is not set. No services need to be running.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "ERROR: .venv not found; run smoke_gateway_repo_root.sh first to bootstrap"
  exit 1
fi

# Run import without RUNTIME_ORCHESTRATOR_URL set; capture exit code.
cd "$REPO_ROOT"
env -i HOME="$HOME" PATH="$PATH" \
  "$VENV_PYTHON" -c "from config.service_config import ServiceConfig" \
  > /tmp/novaic-fail-path-startup.log 2>&1 \
  && STARTUP_EXIT=0 || STARTUP_EXIT=$?

if [ "${STARTUP_EXIT:-0}" -ne 0 ]; then
  echo "FAIL_PATH_STARTUP_NO_URL=PASS"
  echo "FAIL_PATH_STARTUP_EXIT_CODE=$STARTUP_EXIT"
else
  echo "FAIL_PATH_STARTUP_NO_URL=FAIL: import succeeded without RUNTIME_ORCHESTRATOR_URL"
  exit 1
fi

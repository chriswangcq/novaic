#!/usr/bin/env bash
# Failure-path verification: confirms the replay chain exits non-zero when the
# gateway health endpoint is unreachable. No services need to be running.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BAD_GATEWAY_URL="http://127.0.0.1:29999"

GATEWAY_BASE_URL="$BAD_GATEWAY_URL" \
bash "$SCRIPT_DIR/replay_gateway_runtime_chain.sh" \
  > /tmp/novaic-fail-path-test.log 2>&1 \
  && FAIL_EXIT=0 || FAIL_EXIT=$?

if [ "${FAIL_EXIT:-0}" -ne 0 ]; then
  echo "FAIL_PATH_GATEWAY_UNREACHABLE=PASS"
  echo "FAIL_PATH_EXIT_CODE=$FAIL_EXIT"
else
  echo "FAIL_PATH_GATEWAY_UNREACHABLE=FAIL: chain did not exit non-zero with bad gateway URL"
  exit 1
fi

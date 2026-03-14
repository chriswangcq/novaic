#!/usr/bin/env bash
# Failure-path replay: verify all three mandatory service-URL env vars
# produce typed error markers when absent (env -i isolated).
#
# Must be run from the novaic-tools-server repo root.
# Expected final marker: TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_case() {
  local case_name="$1"; shift
  local expected_marker="$1"; shift
  # remaining args are env vars to pass to python
  local output
  output=$(env -i "$@" python3 -c "
import sys; sys.path.insert(0,'${REPO_ROOT}')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok, 'expected ok=False, got ok=True'
assert '${expected_marker}' in r.error, f'expected ${expected_marker} in {r.error!r}'
print('${case_name}:PASS')
" 2>&1)
  echo "$output"
  echo "$output" | grep -q "${case_name}:PASS" || { echo "FAIL: ${case_name}"; exit 1; }
}

# Case 1: GATEWAY_URL missing
run_case "TOOLS_PREFLIGHT_ERROR_GATEWAY_URL" \
  "TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING" \
  "NOVAIC_TOOLS_SERVER_SPLIT_REPO=${REPO_ROOT}" \
  "NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994"

# Case 2: TOOL_RESULT_SERVICE_URL missing
run_case "TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL" \
  "TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING" \
  "NOVAIC_TOOLS_SERVER_SPLIT_REPO=${REPO_ROOT}" \
  "NOVAIC_GATEWAY_URL=http://127.0.0.1:19999"

echo "TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS"

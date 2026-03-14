#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-b-smoke-$$"
DATA_DIR="$TMP_ROOT/data"
LOG_DIR="$TMP_ROOT/logs"
PORT="${STORAGE_B_PORT:-19994}"
HOST="${STORAGE_B_HOST:-127.0.0.1}"
REPORT_PATH="$ROOT_DIR/artifacts/storage-b-smoke-latest.md"

mkdir -p "$DATA_DIR" "$LOG_DIR" "$(dirname "$REPORT_PATH")"
LOG_FILE="$LOG_DIR/storage-b.log"

cleanup() {
  if [[ -n "${SVC_PID:-}" ]]; then kill "$SVC_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

(
  cd "$ROOT_DIR"
  NOVAIC_DATA_DIR="$DATA_DIR" python -m tool_result_service.main --host "$HOST" --port "$PORT" --data-dir "$DATA_DIR" >"$LOG_FILE" 2>&1
) &
SVC_PID=$!

for i in $(seq 1 30); do
  if curl -fsS "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Storage-B service did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done

CREATE_RESP="$(curl -fsS -X POST "http://${HOST}:${PORT}/api/create" \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent-storage-b","tool_name":"smoke-b","text":"ok","files_created":[],"display_files":[]}')"

RESULT_ID="$(python - "$CREATE_RESP" <<'PY'
import json
import sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"

curl -fsS "http://${HOST}:${PORT}/api/${RESULT_ID}" >/dev/null

{
  echo "# Storage-B Smoke Evidence"
  echo
  echo "- command: \`bash scripts/smoke_storage_b.sh\`"
  echo "- expected_marker: \`STORAGE_B_SMOKE_OK=true\`"
  echo "- STORAGE_B_HEALTH=PASS"
  echo "- STORAGE_B_WRITE_READ=PASS"
  echo "- result_id: \`$RESULT_ID\`"
  echo "- log_file: \`$LOG_FILE\`"
} > "$REPORT_PATH"

echo "STORAGE_B_SMOKE_OK=true"
echo "STORAGE_B_EVIDENCE_REPORT=$REPORT_PATH"

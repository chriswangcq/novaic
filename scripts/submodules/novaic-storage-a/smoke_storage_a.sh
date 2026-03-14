#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-a-smoke-$$"
DATA_DIR="$TMP_ROOT/data"
LOG_DIR="$TMP_ROOT/logs"
PORT="${STORAGE_A_PORT:-19995}"
HOST="${STORAGE_A_HOST:-127.0.0.1}"
REPORT_PATH="$ROOT_DIR/artifacts/storage-a-smoke-latest.md"

mkdir -p "$DATA_DIR" "$LOG_DIR" "$(dirname "$REPORT_PATH")"
LOG_FILE="$LOG_DIR/storage-a.log"

cleanup() {
  if [[ -n "${SVC_PID:-}" ]]; then kill "$SVC_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

(
  cd "$ROOT_DIR"
  NOVAIC_DATA_DIR="$DATA_DIR" python -m file_service.main --host "$HOST" --port "$PORT" --base-dir "$DATA_DIR" >"$LOG_FILE" 2>&1
) &
SVC_PID=$!

for i in $(seq 1 30); do
  if curl -fsS "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Storage-A service did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done

CREATE_RESP="$(curl -fsS -X POST "http://${HOST}:${PORT}/api/files/from-base64" \
  -H "Content-Type: application/json" \
  -d '{"data":"c3RvcmFnZS1hLXNtb2tl","agent_id":"agent-storage-a","category":"documents","mime_type":"application/pdf"}')"

FILE_URL="$(python - "$CREATE_RESP" <<'PY'
import json
import sys
print(json.loads(sys.argv[1])["url"])
PY
)"

ENC_FILE_URL="$(python - "$FILE_URL" <<'PY'
import sys
import urllib.parse
print(urllib.parse.quote(sys.argv[1], safe=""))
PY
)"
curl -fsS "http://${HOST}:${PORT}/api/files/info?url=${ENC_FILE_URL}" >/dev/null

REL_PATH="${FILE_URL#/api/files/}"
curl -fsS "http://${HOST}:${PORT}/api/files/${REL_PATH}" >/dev/null

{
  echo "# Storage-A Smoke Evidence"
  echo
  echo "- command: \`bash scripts/smoke_storage_a.sh\`"
  echo "- expected_marker: \`STORAGE_A_SMOKE_OK=true\`"
  echo "- STORAGE_A_HEALTH=PASS"
  echo "- STORAGE_A_WRITE_READ=PASS"
  echo "- file_url: \`$FILE_URL\`"
  echo "- log_file: \`$LOG_FILE\`"
} > "$REPORT_PATH"

echo "STORAGE_A_SMOKE_OK=true"
echo "STORAGE_A_EVIDENCE_REPORT=$REPORT_PATH"

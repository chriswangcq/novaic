#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-ab-smoke-$$"
DATA_DIR="$TMP_ROOT/data"
LOG_DIR="$TMP_ROOT/logs"
REPORT_PATH="$REPO_ROOT/../ops-rounds/round-002/20-reports/team-storage-ab-smoke-latest.md"
FILE_PORT="${FILE_PORT:-29195}"
TRS_PORT="${TRS_PORT:-29194}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--report-path PATH]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$DATA_DIR" "$LOG_DIR"
FILE_LOG="$LOG_DIR/file-service.log"
TRS_LOG="$LOG_DIR/tool-result-service.log"

cleanup() {
  if [[ -n "${FILE_PID:-}" ]]; then kill "$FILE_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${TRS_PID:-}" ]]; then kill "$TRS_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

(
  cd "$REPO_ROOT"
  python -m file_service.main --host 127.0.0.1 --port "$FILE_PORT" --base-dir "$DATA_DIR" >"$FILE_LOG" 2>&1
) &
FILE_PID=$!

(
  cd "$REPO_ROOT"
  NOVAIC_DATA_DIR="$DATA_DIR" python -m tool_result_service.main --host 127.0.0.1 --port "$TRS_PORT" --data-dir "$DATA_DIR" >"$TRS_LOG" 2>&1
) &
TRS_PID=$!

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${FILE_PORT}/api/health" >/dev/null 2>&1 && \
     curl -fsS "http://127.0.0.1:${TRS_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Services did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done

FILE_CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${FILE_PORT}/api/files/from-base64" \
  -H "Content-Type: application/json" \
  -d '{"data":"aGVsbG8tc3RvcmFnZS1hYi1zbW9rZQ==","agent_id":"agent-smoke","category":"documents","mime_type":"application/pdf"}')"
FILE_URL="$(python - "$FILE_CREATE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["url"])
PY
)"

ENC_FILE_URL="$(python - "$FILE_URL" <<'PY'
import sys, urllib.parse
print(urllib.parse.quote(sys.argv[1], safe=""))
PY
)"
curl -fsS "http://127.0.0.1:${FILE_PORT}/api/files/info?url=${ENC_FILE_URL}" >/dev/null

REL_PATH="${FILE_URL#/api/files/}"
curl -fsS "http://127.0.0.1:${FILE_PORT}/api/files/${REL_PATH}" >/dev/null

TRS_CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${TRS_PORT}/api/create" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"agent-smoke\",\"tool_name\":\"smoke-tool\",\"text\":\"ok\",\"files_created\":[{\"url\":\"${FILE_URL}\",\"filename\":\"smoke.pdf\",\"modality\":\"resource\"}],\"display_files\":[]}")"
RESULT_ID="$(python - "$TRS_CREATE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"
curl -fsS "http://127.0.0.1:${TRS_PORT}/api/${RESULT_ID}" >/dev/null

mkdir -p "$(dirname "$REPORT_PATH")"
{
  echo "# Storage-A/B Smoke Evidence"
  echo
  echo "- status: DONE"
  echo "- executed_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- command: \`bash novaic-backend/scripts/storage_ab_smoke.sh\`"
  echo "- file_service_health: PASS"
  echo "- tool_result_service_health: PASS"
  echo "- file_write_read: PASS"
  echo "- tool_result_write_read: PASS"
  echo "- file_url: \`$FILE_URL\`"
  echo "- result_id: \`$RESULT_ID\`"
  echo "- logs:"
  echo "  - \`$FILE_LOG\`"
  echo "  - \`$TRS_LOG\`"
} > "$REPORT_PATH"

echo "SMOKE_OK=true"
echo "EVIDENCE_REPORT=$REPORT_PATH"

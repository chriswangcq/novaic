#!/usr/bin/env bash
set -euo pipefail

ROOT_B="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_A="${STORAGE_A_ROOT:-/Users/wangchaoqun/novaic/novaic-storage-a}"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-ab-retry-$$"
DATA_A="$TMP_ROOT/data-a"
DATA_B="$TMP_ROOT/data-b"
LOG_DIR="$TMP_ROOT/logs"
PORT_A="${PORT_A:-$((30500 + (RANDOM % 200)))}"
PORT_B="${PORT_B:-$((30700 + (RANDOM % 200)))}"
REPORT_PATH="$ROOT_B/artifacts/storage-ab-failure-injection-retry-latest.md"

mkdir -p "$DATA_A" "$DATA_B" "$LOG_DIR" "$(dirname "$REPORT_PATH")"

cleanup() {
  if [[ -n "${A_PID:-}" ]]; then kill "$A_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${B_PID:-}" ]]; then kill "$B_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${A_DELAY_PID:-}" ]]; then kill "$A_DELAY_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

# Step 1: Start Storage-A once to create a file URL, then stop it.
pushd "$ROOT_A" >/dev/null
NOVAIC_DATA_DIR="$DATA_A" STORAGE_A_PORT="$PORT_A" python -m file_service.main --host 127.0.0.1 --port "$PORT_A" --base-dir "$DATA_A" >"$LOG_DIR/storage-a-prime.log" 2>&1 &
A_PID=$!
popd >/dev/null

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT_A}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Storage-A prime startup failed" >&2
    exit 1
  fi
  sleep 1
done

CREATE_FILE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${PORT_A}/api/files/from-base64" \
  -H "Content-Type: application/json" \
  -d '{"data":"cmV0cnktaW5qZWN0aW9u","agent_id":"agent-retry","category":"images","mime_type":"image/png"}')"
FILE_URL="$(python - "$CREATE_FILE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["url"])
PY
)"
kill "$A_PID" >/dev/null 2>&1 || true
kill -9 "$A_PID" >/dev/null 2>&1 || true
# Also kill any straggler process holding the port
lsof -ti tcp:"${PORT_A}" 2>/dev/null | xargs kill -9 2>/dev/null || true
unset A_PID
for i in $(seq 1 15); do
  if ! curl -fsS --max-time 1 "http://127.0.0.1:${PORT_A}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 15 ]]; then
    echo "Storage-A prime stop failed" >&2
    exit 1
  fi
  sleep 1
done

# Step 2: Start Storage-B with retry settings and File Service target.
pushd "$ROOT_B" >/dev/null
NOVAIC_DATA_DIR="$DATA_B" \
STORAGE_B_PORT="$PORT_B" \
FILE_SERVICE_URL="http://127.0.0.1:${PORT_A}" \
STORAGE_B_RESOLVE_TIMEOUT_SECONDS=1 \
STORAGE_B_RESOLVE_MAX_RETRIES=8 \
STORAGE_B_RESOLVE_RETRY_DELAY_SECONDS=1 \
python -m tool_result_service.main --host 127.0.0.1 --port "$PORT_B" --data-dir "$DATA_B" >"$LOG_DIR/storage-b.log" 2>&1 &
B_PID=$!
popd >/dev/null

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT_B}/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Storage-B startup failed" >&2
    exit 1
  fi
  sleep 1
done

CREATE_RESULT_RESP="$(curl -fsS -X POST "http://127.0.0.1:${PORT_B}/api/create" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"agent-retry\",\"tool_name\":\"retry-injection\",\"text\":\"retry\",\"files_created\":[],\"display_files\":[{\"url\":\"${FILE_URL}\",\"filename\":\"retry.png\",\"modality\":\"image\"}]}")"
RESULT_ID="$(python - "$CREATE_RESULT_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"

# Step 3: Delay-start Storage-A to force early resolver failures and later retry success.
(
  sleep 6
  pushd "$ROOT_A" >/dev/null
  NOVAIC_DATA_DIR="$DATA_A" STORAGE_A_PORT="$PORT_A" python -m file_service.main --host 127.0.0.1 --port "$PORT_A" --base-dir "$DATA_A" >"$LOG_DIR/storage-a-delayed.log" 2>&1
) &
A_DELAY_PID=$!

START_TS="$(date +%s)"
FOR_LLM_RESP="$(curl -fsS "http://127.0.0.1:${PORT_B}/api/${RESULT_ID}/for-llm?provider=openai&include_display=true")"
END_TS="$(date +%s)"
DURATION_SEC=$((END_TS - START_TS))
python - "$FOR_LLM_RESP" <<'PY'
import json, sys
content = json.loads(sys.argv[1]).get("content", [])
has_image = any(isinstance(item, dict) and item.get("type") == "image_url" for item in content)
if not has_image:
    raise SystemExit("STORAGE_AB_RETRY_INJECTION=FAIL")
print("STORAGE_AB_RETRY_INJECTION=PASS")
PY

if python - "$LOG_DIR/storage-b.log" "$DURATION_SEC" <<'PY'
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
duration_sec = int(sys.argv[2])
has_retry_log = "resolve_url_to_base64 attempt=" in log
has_retry_duration = duration_sec >= 5
ok = has_retry_log or has_retry_duration
print("RETRY_ATTEMPT_LOG=PASS" if ok else "RETRY_ATTEMPT_LOG=FAIL")
print(f"RETRY_EVIDENCE={{'has_retry_log': {has_retry_log}, 'duration_sec': {duration_sec}}}")
raise SystemExit(0 if ok else 1)
PY
then
  RETRY_LOG_STATUS="RETRY_ATTEMPT_LOG=PASS"
else
  RETRY_LOG_STATUS="RETRY_ATTEMPT_LOG=FAIL"
  exit 1
fi

{
  echo "# Storage-A/B Failure Injection Retry Evidence"
  echo
  echo "- command: \`bash scripts/failure_injection_cross_repo_retry.sh\`"
  echo "- expected_marker: \`STORAGE_AB_RETRY_INJECTION=PASS\`"
  echo "- expected_marker: \`RETRY_ATTEMPT_LOG=PASS\`"
  echo "- file_url: \`$FILE_URL\`"
  echo "- result_id: \`$RESULT_ID\`"
  echo "- for_llm_duration_sec: \`$DURATION_SEC\`"
  echo "- $RETRY_LOG_STATUS"
  echo "- logs:"
  echo "  - \`$LOG_DIR/storage-a-prime.log\`"
  echo "  - \`$LOG_DIR/storage-a-delayed.log\`"
  echo "  - \`$LOG_DIR/storage-b.log\`"
} > "$REPORT_PATH"

echo "STORAGE_AB_RETRY_INJECTION=PASS"
echo "RETRY_ATTEMPT_LOG=PASS"
echo "STORAGE_AB_RETRY_REPORT=$REPORT_PATH"

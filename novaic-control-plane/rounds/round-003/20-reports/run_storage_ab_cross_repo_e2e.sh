#!/usr/bin/env bash
set -euo pipefail

TMP_ROOT="${TMPDIR:-/tmp}/novaic-round003-storage-e2e-$$"
DATA_A="$TMP_ROOT/data-a"
DATA_B="$TMP_ROOT/data-b"
LOG_DIR="$TMP_ROOT/logs"
REPORT_PATH="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/20-reports/team-storage-ab-cross-repo-e2e.md"

mkdir -p "$DATA_A" "$DATA_B" "$LOG_DIR" "$(dirname "$REPORT_PATH")"

(
  cd "/Users/wangchaoqun/novaic/novaic-storage-a"
  NOVAIC_DATA_DIR="$DATA_A" STORAGE_A_PORT=29295 python -m file_service.main --host 127.0.0.1 --port 29295 --base-dir "$DATA_A" >"$LOG_DIR/storage-a.log" 2>&1
) &
PID_A=$!

(
  cd "/Users/wangchaoqun/novaic/novaic-storage-b"
  NOVAIC_DATA_DIR="$DATA_B" STORAGE_B_PORT=29294 FILE_SERVICE_URL="http://127.0.0.1:29295" python -m tool_result_service.main --host 127.0.0.1 --port 29294 --data-dir "$DATA_B" >"$LOG_DIR/storage-b.log" 2>&1
) &
PID_B=$!

cleanup() {
  kill "$PID_A" "$PID_B" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:29295/api/health" >/dev/null 2>&1 && curl -fsS "http://127.0.0.1:29294/api/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "E2E_READY=FAIL" >&2
    exit 1
  fi
  sleep 1
done

FILE_CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:29295/api/files/from-base64" -H "Content-Type: application/json" -d '{"data":"aW1hZ2UtYnl0ZXM=","agent_id":"agent-e2e","category":"images","mime_type":"image/png"}')"
FILE_URL="$(python - "$FILE_CREATE_RESP" <<'PY'
import json,sys
print(json.loads(sys.argv[1])["url"])
PY
)"

CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:29294/api/create" -H "Content-Type: application/json" -d "{\"agent_id\":\"agent-e2e\",\"tool_name\":\"cross-repo-e2e\",\"text\":\"chain\",\"files_created\":[],\"display_files\":[{\"url\":\"$FILE_URL\",\"filename\":\"img.png\",\"modality\":\"image\"}]}")"
RESULT_ID="$(python - "$CREATE_RESP" <<'PY'
import json,sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"

FOR_LLM_RESP="$(curl -fsS "http://127.0.0.1:29294/api/$RESULT_ID/for-llm?provider=openai&include_display=true")"
python - "$FOR_LLM_RESP" <<'PY'
import json,sys
obj=json.loads(sys.argv[1])
content=obj.get("content",[])
has_image=any(isinstance(item,dict) and item.get("type")=="image_url" for item in content)
if not has_image:
    raise SystemExit("CROSS_REPO_CHAIN=FAIL")
print("CROSS_REPO_CHAIN=PASS")
PY

{
  echo "# Storage-A/B Cross Repo E2E"
  echo
  echo "- command: storage-a + storage-b startup and /for-llm replay"
  echo "- expected_marker: \`CROSS_REPO_CHAIN=PASS\`"
  echo "- file_service_health: PASS"
  echo "- tool_result_service_health: PASS"
  echo "- cross_repo_chain: PASS"
  echo "- file_url: \`$FILE_URL\`"
  echo "- result_id: \`$RESULT_ID\`"
  echo "- log_a: \`$LOG_DIR/storage-a.log\`"
  echo "- log_b: \`$LOG_DIR/storage-b.log\`"
} > "$REPORT_PATH"

echo "CROSS_REPO_CHAIN=PASS"
echo "E2E_REPORT=$REPORT_PATH"

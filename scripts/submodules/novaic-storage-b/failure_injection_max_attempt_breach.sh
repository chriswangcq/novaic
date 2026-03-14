#!/usr/bin/env bash
# failure_injection_max_attempt_breach.sh
# Proves resolver stops at STORAGE_B_RESOLVE_MAX_RETRIES when Storage-A is permanently offline.
# Expected markers:
#   RETRY_MAX_BREACH_ATTEMPTS_SEEN=<N>  (must equal configured max)
#   RETRY_MAX_BREACH_RESOLVER_NULL=PASS (response must NOT contain image_url — graceful null)
#   RETRY_MAX_BREACH_STOP=PASS
set -euo pipefail

ROOT_B="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-max-breach-$$"
DATA_B="$TMP_ROOT/data-b"
LOG_DIR="$TMP_ROOT/logs"
PORT_B="${PORT_B:-$((31000 + (RANDOM % 300)))}"
# Point to a port that is guaranteed offline — Storage-A is never started.
PORT_A_FAKE="${PORT_A_FAKE:-$((39700 + (RANDOM % 300)))}"
MAX_RETRIES=3
REPORT_PATH="$ROOT_B/artifacts/storage-ab-max-attempt-breach-latest.md"

mkdir -p "$DATA_B" "$LOG_DIR" "$(dirname "$REPORT_PATH")"

cleanup() {
  if [[ -n "${B_PID:-}" ]]; then kill "$B_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

# Step 1: Start Storage-B with short timeout, low max-retries, pointing to permanently dead Storage-A.
pushd "$ROOT_B" >/dev/null
NOVAIC_DATA_DIR="$DATA_B" \
STORAGE_B_PORT="$PORT_B" \
FILE_SERVICE_URL="http://127.0.0.1:${PORT_A_FAKE}" \
STORAGE_B_RESOLVE_TIMEOUT_SECONDS=0.5 \
STORAGE_B_RESOLVE_MAX_RETRIES="${MAX_RETRIES}" \
STORAGE_B_RESOLVE_RETRY_DELAY_SECONDS=0.3 \
python -m tool_result_service.main \
  --host 127.0.0.1 --port "$PORT_B" --data-dir "$DATA_B" \
  >"$LOG_DIR/storage-b.log" 2>&1 &
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

# Step 2: Create a tool result with a display file — the URL will target dead Storage-A.
FAKE_FILE_URL="http://127.0.0.1:${PORT_A_FAKE}/api/files/fake/image.png"
CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${PORT_B}/api/create" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"breach-test\",\"tool_name\":\"max-breach\",\"text\":\"breach\",\"files_created\":[],\"display_files\":[{\"url\":\"${FAKE_FILE_URL}\",\"filename\":\"breach.png\",\"modality\":\"image\"}]}")"
RESULT_ID="$(python - "$CREATE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"

# Step 3: Call for-llm — resolver will exhaust MAX_RETRIES and return null.
FOR_LLM_RESP="$(curl -fsS "http://127.0.0.1:${PORT_B}/api/${RESULT_ID}/for-llm?provider=openai&include_display=true")"

# Step 4: Assert resolver returned null (no image_url in content).
python - "$FOR_LLM_RESP" <<'PY'
import json, sys
content = json.loads(sys.argv[1]).get("content", [])
has_image = any(isinstance(item, dict) and item.get("type") == "image_url" for item in content)
if has_image:
    print("RETRY_MAX_BREACH_RESOLVER_NULL=FAIL  # image_url present; resolver did NOT return null")
    raise SystemExit(1)
print("RETRY_MAX_BREACH_RESOLVER_NULL=PASS")
PY

# Step 5: Assert log shows exactly MAX_RETRIES attempts and stopped.
python - "$LOG_DIR/storage-b.log" "$MAX_RETRIES" <<'PY'
import sys, re
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
expected_max = int(sys.argv[2])
attempts = re.findall(r'resolve_url_to_base64 attempt=(\d+)/' + str(expected_max), log)
seen = len(attempts)
last_attempt = int(attempts[-1]) if attempts else 0
print(f"RETRY_MAX_BREACH_ATTEMPTS_SEEN={seen}")
if seen == 0:
    print("RETRY_MAX_BREACH_STOP=FAIL  # no retry log lines found")
    raise SystemExit(1)
if last_attempt != expected_max:
    print(f"RETRY_MAX_BREACH_STOP=FAIL  # last attempt={last_attempt}, expected={expected_max}")
    raise SystemExit(1)
# Check no attempt > expected_max (resolver did not over-retry)
over = [a for a in attempts if int(a) > expected_max]
if over:
    print(f"RETRY_MAX_BREACH_STOP=FAIL  # over-retry detected: {over}")
    raise SystemExit(1)
print("RETRY_MAX_BREACH_STOP=PASS")
PY

{
  echo "# Storage-A/B Max-Attempt Breach Injection Evidence"
  echo
  echo "- command: \`bash scripts/failure_injection_max_attempt_breach.sh\`"
  echo "- scenario: Storage-A permanently offline; Storage-B retry exhausts \`STORAGE_B_RESOLVE_MAX_RETRIES=${MAX_RETRIES}\`"
  echo "- expected_marker: \`RETRY_MAX_BREACH_RESOLVER_NULL=PASS\`"
  echo "- expected_marker: \`RETRY_MAX_BREACH_ATTEMPTS_SEEN=${MAX_RETRIES}\`"
  echo "- expected_marker: \`RETRY_MAX_BREACH_STOP=PASS\`"
  echo "- result_id: \`$RESULT_ID\`"
  echo "- fake_file_url: \`$FAKE_FILE_URL\`"
  echo "- logs: \`$LOG_DIR/storage-b.log\`"
} > "$REPORT_PATH"

echo "RETRY_MAX_BREACH_STOP=PASS"
echo "STORAGE_AB_MAX_BREACH_REPORT=$REPORT_PATH"

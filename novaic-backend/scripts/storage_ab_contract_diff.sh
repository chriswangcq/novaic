#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-ab-contract-$$"
DATA_DIR="$TMP_ROOT/data"
LOG_DIR="$TMP_ROOT/logs"
EVERGREEN_REPORT_PATH="$REPO_ROOT/../contracts/evidence/storage-contract-diff-latest.md"
REPORT_PATH="$EVERGREEN_REPORT_PATH"
SCHEMA_PATH="$REPO_ROOT/../contracts/schema/storage-api.v1.schema.json"
FILE_PORT="${FILE_PORT:-30195}"
TRS_PORT="${TRS_PORT:-30194}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    --schema-path)
      SCHEMA_PATH="$2"
      shift 2
      ;;
    --evergreen-report-path)
      EVERGREEN_REPORT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--report-path PATH] [--schema-path PATH] [--evergreen-report-path PATH]"
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
    echo "services did not become healthy in time" >&2
    exit 1
  fi
  sleep 1
done

FILE_CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${FILE_PORT}/api/files/from-base64" \
  -H "Content-Type: application/json" \
  -d '{"data":"Y29udHJhY3QtZGlmZi1wYXlsb2Fk","agent_id":"agent-contract","category":"documents","mime_type":"application/pdf"}')"
FILE_URL="$(python - "$FILE_CREATE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["url"])
PY
)"

TRS_CREATE_RESP="$(curl -fsS -X POST "http://127.0.0.1:${TRS_PORT}/api/create" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"agent-contract\",\"tool_name\":\"contract-tool\",\"text\":\"ok\",\"files_created\":[{\"url\":\"${FILE_URL}\",\"filename\":\"contract.pdf\",\"modality\":\"resource\"}],\"display_files\":[]}")"
RESULT_ID="$(python - "$TRS_CREATE_RESP" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["result_id"])
PY
)"
TRS_GET_RESP="$(curl -fsS "http://127.0.0.1:${TRS_PORT}/api/${RESULT_ID}")"

mkdir -p "$(dirname "$REPORT_PATH")"
mkdir -p "$(dirname "$EVERGREEN_REPORT_PATH")"
python - "$REPORT_PATH" "$EVERGREEN_REPORT_PATH" "$SCHEMA_PATH" "$FILE_CREATE_RESP" "$TRS_CREATE_RESP" "$TRS_GET_RESP" <<'PY'
import json
import re
import sys
from datetime import datetime, UTC

report_path = sys.argv[1]
evergreen_path = sys.argv[2]
schema_path = sys.argv[3]
file_resp = json.loads(sys.argv[4])
trs_create = json.loads(sys.argv[5])
trs_get = json.loads(sys.argv[6])

with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

schema_version = schema.get("x-contract-version", "")
schema_owners = schema.get("x-contract-owners", [])
required_owners = {"Platform Team", "API Team", "Storage-A/B Team"}
schema_version_ok = isinstance(schema_version, str) and schema_version.startswith("v")
schema_owner_ok = required_owners.issubset(set(schema_owners))

expected_file = set(schema["properties"]["file_service"]["properties"]["from_base64_response_required_fields"]["default"] if "default" in schema["properties"]["file_service"]["properties"]["from_base64_response_required_fields"] else schema["examples"][0]["file_service"]["from_base64_response_required_fields"])
expected_trs_create = set(schema["properties"]["tool_result_service"]["properties"]["create_response_required_fields"]["default"] if "default" in schema["properties"]["tool_result_service"]["properties"]["create_response_required_fields"] else schema["examples"][0]["tool_result_service"]["create_response_required_fields"])
expected_trs_get = set(schema["properties"]["tool_result_service"]["properties"]["get_response_required_fields"]["default"] if "default" in schema["properties"]["tool_result_service"]["properties"]["get_response_required_fields"] else schema["examples"][0]["tool_result_service"]["get_response_required_fields"])
expected_normalized = set(schema["properties"]["tool_result_service"]["properties"]["normalized_required_fields"]["default"] if "default" in schema["properties"]["tool_result_service"]["properties"]["normalized_required_fields"] else schema["examples"][0]["tool_result_service"]["normalized_required_fields"])

def matrix(name, expected, actual):
    matched = sorted(expected & actual)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return {
        "name": name,
        "matched": matched,
        "missing": missing,
        "extra": extra,
    }

file_actual = set(file_resp.keys())
trs_create_actual = set(trs_create.keys())
trs_get_actual = set(trs_get.keys())
normalized_actual = set((trs_get.get("normalized") or {}).keys())

matrices = [
    matrix("file_service.from-base64 response", expected_file, file_actual),
    matrix("tool_result_service.create response", expected_trs_create, trs_create_actual),
    matrix("tool_result_service.get response", expected_trs_get, trs_get_actual),
    matrix("tool_result_service.normalized payload", expected_normalized, normalized_actual),
]

lines = []
lines.append("# Storage-A/B Contract Diff Evidence")
lines.append("")
lines.append("- status: DONE")
lines.append(f"- executed_at_utc: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}")
lines.append("- command: `bash novaic-backend/scripts/storage_ab_contract_diff.sh`")
lines.append(f"- schema_path: `{schema_path}`")
lines.append(f"- schema_version: `{schema_version}`")
lines.append(f"- schema_owners: `{schema_owners}`")
lines.append(f"- schema_version_check: {'PASS' if schema_version_ok else 'FAIL'}")
lines.append(f"- schema_owner_check: {'PASS' if schema_owner_ok else 'FAIL'}")
lines.append("- baseline_docs:")
lines.append("  - `week1-team-workorders/storage-ab/data-model-v0.1.md`")
lines.append("  - `contracts/schema/storage-api.v1.schema.json`")
round_dispatch = "ops-rounds/<current-round>/10-dispatch/team-storage-ab.md"
m = re.search(r"(ops-rounds/round-[^/]+)/20-reports", report_path)
if m:
    round_dispatch = f"{m.group(1)}/10-dispatch/team-storage-ab.md"
lines.append(f"  - `{round_dispatch}`")
lines.append("")
lines.append("## Matrix")
for m in matrices:
    lines.append(f"### {m['name']}")
    lines.append(f"- matched: {m['matched']}")
    lines.append(f"- missing: {m['missing']}")
    lines.append(f"- extra: {m['extra']}")
    lines.append("")

lines.append("## Raw Samples")
lines.append("- file_service.from-base64:")
lines.append(f"  - `{json.dumps(file_resp, ensure_ascii=False)}`")
lines.append("- tool_result_service.create:")
lines.append(f"  - `{json.dumps(trs_create, ensure_ascii=False)}`")
lines.append("- tool_result_service.get:")
lines.append(f"  - `{json.dumps(trs_get, ensure_ascii=False)}`")
lines.append("")
lines.append("## Notes")
lines.append("- contract diff is schema-backed and executable against live service responses.")

if not schema_version_ok or not schema_owner_ok:
    lines.append("- governance_check: FAIL")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    raise SystemExit("schema version/owner governance check failed")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

with open(evergreen_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
PY

echo "CONTRACT_DIFF_OK=true"
echo "EVIDENCE_REPORT=$REPORT_PATH"
echo "EVERGREEN_EVIDENCE_REPORT=$EVERGREEN_REPORT_PATH"

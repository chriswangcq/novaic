#!/usr/bin/env bash
# verify_contract_version_b.sh
# Starts Storage-B, checks /api/health returns contract_version=storage-b/v1
# Expected markers:
#   STORAGE_B_CONTRACT_VERSION_FIELD=PASS
#   STORAGE_B_CONTRACT_VERSION=PASS
set -uo pipefail

ROOT_B="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-b-contract-$$"
DATA_B="$TMP_ROOT/data"
PORT_B="${PORT_B:-$((32500 + (RANDOM % 300)))}"

mkdir -p "$DATA_B"
cleanup() { if [[ -n "${B_PID:-}" ]]; then kill "$B_PID" >/dev/null 2>&1 || true; fi; }
trap cleanup EXIT

pushd "$ROOT_B" >/dev/null
NOVAIC_DATA_DIR="$DATA_B" STORAGE_B_PORT="$PORT_B" \
  python -m tool_result_service.main --host 127.0.0.1 --port "$PORT_B" --data-dir "$DATA_B" \
  >/dev/null 2>&1 &
B_PID=$!
popd >/dev/null

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT_B}/api/health" >/dev/null 2>&1; then break; fi
  [[ "$i" -eq 30 ]] && { echo "Storage-B startup failed" >&2; exit 1; }
  sleep 1
done

HEALTH_JSON="$(curl -fsS "http://127.0.0.1:${PORT_B}/api/health")"

python - "$HEALTH_JSON" <<'PY'
import json, sys
body = json.loads(sys.argv[1])
field_present = "contract_version" in body
version_correct = body.get("contract_version") == "storage-b/v1"
print("STORAGE_B_CONTRACT_VERSION_FIELD=PASS" if field_present else "STORAGE_B_CONTRACT_VERSION_FIELD=FAIL")
print("STORAGE_B_CONTRACT_VERSION=PASS" if version_correct else f"STORAGE_B_CONTRACT_VERSION=FAIL  # got {body.get('contract_version')!r}")
if not (field_present and version_correct):
    raise SystemExit(1)
PY

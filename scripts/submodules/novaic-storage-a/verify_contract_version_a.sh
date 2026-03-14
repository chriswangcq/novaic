#!/usr/bin/env bash
# verify_contract_version_a.sh
# Starts Storage-A, checks /api/health returns contract_version=storage-a/v1
# Expected markers:
#   STORAGE_A_CONTRACT_VERSION_FIELD=PASS
#   STORAGE_A_CONTRACT_VERSION=PASS
set -uo pipefail

ROOT_A="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-a-contract-$$"
DATA_A="$TMP_ROOT/data"
PORT_A="${PORT_A:-$((32000 + (RANDOM % 300)))}"

mkdir -p "$DATA_A"
cleanup() { if [[ -n "${A_PID:-}" ]]; then kill "$A_PID" >/dev/null 2>&1 || true; fi; }
trap cleanup EXIT

pushd "$ROOT_A" >/dev/null
NOVAIC_DATA_DIR="$DATA_A" STORAGE_A_PORT="$PORT_A" \
  python -m file_service.main --host 127.0.0.1 --port "$PORT_A" --base-dir "$DATA_A" \
  >/dev/null 2>&1 &
A_PID=$!
popd >/dev/null

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT_A}/api/health" >/dev/null 2>&1; then break; fi
  [[ "$i" -eq 30 ]] && { echo "Storage-A startup failed" >&2; exit 1; }
  sleep 1
done

HEALTH_JSON="$(curl -fsS "http://127.0.0.1:${PORT_A}/api/health")"

python - "$HEALTH_JSON" <<'PY'
import json, sys
body = json.loads(sys.argv[1])
field_present = "contract_version" in body
version_correct = body.get("contract_version") == "storage-a/v1"
print("STORAGE_A_CONTRACT_VERSION_FIELD=PASS" if field_present else "STORAGE_A_CONTRACT_VERSION_FIELD=FAIL")
print("STORAGE_A_CONTRACT_VERSION=PASS" if version_correct else f"STORAGE_A_CONTRACT_VERSION=FAIL  # got {body.get('contract_version')!r}")
if not (field_present and version_correct):
    raise SystemExit(1)
PY

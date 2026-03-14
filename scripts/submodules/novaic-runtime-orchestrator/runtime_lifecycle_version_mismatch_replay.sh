#!/usr/bin/env bash
# Version-mismatch failure-path replay.
# Temporarily overwrites contract/runtime-contract-version.json with a wrong
# version, runs the lifecycle guard, and asserts it exits non-zero with the
# deterministic marker:
#   FAIL: contract version mismatch: file=v99 expected=v1
#
# Expected marker: FAIL: contract version mismatch: file=v99 expected=v1
set -euo pipefail

cd "$(dirname "$0")/.."

export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

CONTRACT_FILE="contract/runtime-contract-version.json"
BACKUP_FILE="/tmp/runtime-contract-version.json.bak"

# Save real contract file and restore it on exit
cp "${CONTRACT_FILE}" "${BACKUP_FILE}"
restore_contract() {
  cp "${BACKUP_FILE}" "${CONTRACT_FILE}"
}
trap restore_contract EXIT

# Inject wrong version
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("contract/runtime-contract-version.json").read_text(encoding="utf-8"))
data["version"] = "v99"
Path("contract/runtime-contract-version.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
PY

# Run the guard — it must fail because file version v99 != expected v1
GUARD_OUTPUT="$(bash scripts/runtime_lifecycle_contract_guard_replay.sh 2>&1)" && GUARD_EXIT=0 || GUARD_EXIT=$?

echo "${GUARD_OUTPUT}"

if [ "${GUARD_EXIT}" -eq 0 ]; then
  echo "FAIL: version-mismatch-replay expected non-zero exit but guard succeeded — contract version check is broken"
  exit 1
fi

# Verify deterministic FAIL marker is present in output
if echo "${GUARD_OUTPUT}" | grep -qF "FAIL: contract version mismatch: file=v99 expected=v1"; then
  echo "FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)"
  echo "PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version"
else
  echo "FAIL: version-mismatch-replay output did not contain expected FAIL marker"
  echo "actual output: ${GUARD_OUTPUT}"
  exit 1
fi

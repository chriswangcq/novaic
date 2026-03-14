#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

PORT="$(python - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path("config/services.json").read_text(encoding="utf-8"))
print(cfg["services"]["runtime_orchestrator"]["port"])
PY
)"

BASE_URL="http://127.0.0.1:${PORT}"
LOG_FILE="/tmp/novaic-runtime-orchestrator-lifecycle-guard.log"
PID=""

cleanup() {
  set +e
  if [ -n "$PID" ]; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Read contract version from tracked source-of-truth file (not hardcoded).
EXPECTED_CONTRACT_VERSION="v2"
RUNTIME_CONTRACT_VERSION="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("contract/runtime-contract-version.json").read_text(encoding="utf-8"))
print(data["version"])
PY
)"
export RUNTIME_CONTRACT_VERSION

if [ "${RUNTIME_CONTRACT_VERSION}" != "${EXPECTED_CONTRACT_VERSION}" ]; then
  echo "FAIL: contract version mismatch: file=${RUNTIME_CONTRACT_VERSION} expected=${EXPECTED_CONTRACT_VERSION}"
  exit 1
fi
echo "RUNTIME_CONTRACT_VERSION=${RUNTIME_CONTRACT_VERSION}"

python main_runtime_orchestrator.py runtime-orchestrator >"$LOG_FILE" 2>&1 &
PID="$!"

python - <<'PY'
import json
import os
import time
import httpx
from pathlib import Path

cfg = json.loads(Path("config/services.json").read_text(encoding="utf-8"))
port = cfg["services"]["runtime_orchestrator"]["port"]
base = f"http://127.0.0.1:{port}"
client = httpx.Client(timeout=5.0, trust_env=False)

deadline = time.time() + 30
while time.time() < deadline:
    try:
        r = client.get(f"{base}/api/health")
        if r.status_code == 200 and r.json().get("status") == "ok":
            break
    except Exception:
        pass
    time.sleep(0.25)
else:
    raise SystemExit("FAIL: runtime lifecycle contract guard startup health timeout")

agent_id = "guard-agent-round005"
r = client.get(f"{base}/internal/subagents/{agent_id}/main")
assert r.status_code == 200, "subagent bootstrap endpoint unavailable"
subagent_id = r.json().get("subagent_id")
assert subagent_id, "subagent bootstrap response missing subagent_id"
payload = {"agent_id": agent_id, "subagent_id": subagent_id}
r = client.post(f"{base}/internal/runtimes/get-or-create", json=payload)
assert r.status_code == 200, f"get-or-create endpoint unavailable: {r.status_code} {r.text}"
runtime = r.json()
runtime_id = runtime.get("runtime_id")
assert runtime_id, "runtime_id missing in get-or-create response"
assert runtime.get("status") == "active", "get-or-create no longer returns active runtime"

r = client.post(
    f"{base}/internal/runtimes/{runtime_id}/set-status",
    json={"expected_status": ["active"], "new_status": "completed"},
)
assert r.status_code == 200 and r.json().get("success") is True, "set-status contract broken"

# Verify contract version loaded from file matches expected
contract_version = os.environ.get("RUNTIME_CONTRACT_VERSION", "")
assert contract_version == "v2", f"FAIL: unexpected contract version: {contract_version}"

print("PASS: runtime lifecycle contract guard replay")
print(f"PASS: contract runtime_id {runtime_id}")
print("PASS: RUNTIME_CONTRACT_VERSION=v2")
PY

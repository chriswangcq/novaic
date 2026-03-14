#!/usr/bin/env bash
# Failure-path replay: validates that invalid lifecycle state transitions are
# deterministically rejected by the CAS set-status endpoint.
#
# Expected deterministic marker: FAIL-MARKER: invalid-transition-cas-rejected
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
LOG_FILE="/tmp/novaic-runtime-orchestrator-failure-path.log"
PID=""

cleanup() {
  set +e
  if [ -n "$PID" ]; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python main_runtime_orchestrator.py runtime-orchestrator >"$LOG_FILE" 2>&1 &
PID="$!"

python - <<'PY'
import json
import time
import httpx
from pathlib import Path

cfg = json.loads(Path("config/services.json").read_text(encoding="utf-8"))
port = cfg["services"]["runtime_orchestrator"]["port"]
base = f"http://127.0.0.1:{port}"
client = httpx.Client(timeout=5.0, trust_env=False)

# Wait for service to be healthy
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
    raise SystemExit("FAIL: failure-path replay startup health timeout")

# Bootstrap: create an active runtime
agent_id = "failure-path-guard-agent"
r = client.get(f"{base}/internal/subagents/{agent_id}/main")
assert r.status_code == 200, f"subagent bootstrap failed: {r.status_code}"
subagent_id = r.json().get("subagent_id")
assert subagent_id, "subagent_id missing"

r = client.post(f"{base}/internal/runtimes/get-or-create",
                json={"agent_id": agent_id, "subagent_id": subagent_id})
assert r.status_code == 200, f"get-or-create failed: {r.status_code}"
runtime_id = r.json().get("runtime_id")
assert runtime_id, "runtime_id missing"
current_status = r.json().get("status")
assert current_status == "active", f"expected active runtime, got: {current_status}"

# FAILURE PATH: attempt set-status with wrong expected_status.
# Runtime is currently "active", but we claim expected_status=["completed"]
# and request new_status="failed". CAS must reject because current != expected.
# The idempotency short-circuit only fires when current_status == new_status,
# which is not the case here ("active" != "failed").
r = client.post(
    f"{base}/internal/runtimes/{runtime_id}/set-status",
    json={"expected_status": ["completed"], "new_status": "failed"},
)
# The endpoint returns success:false when CAS fails (status mismatch)
assert r.status_code == 200, f"set-status unexpected HTTP error: {r.status_code}"
body = r.json()
success = body.get("success")
current = body.get("current_status", "unknown")
assert success is False, (
    f"FAIL: expected CAS rejection (success=false) but got success={success}. "
    f"This means the invalid transition was accepted — contract broken."
)

print(f"FAIL-MARKER: invalid-transition-cas-rejected (current_status={current})")
print("PASS: failure-path replay confirmed CAS correctly rejects invalid lifecycle transition")
PY

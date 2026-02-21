#!/usr/bin/env bash
set -euo pipefail

GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://127.0.0.1:20000}"
RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://127.0.0.1:20001}"

runtime_payload="$(curl --noproxy '*' -fsS "$RUNTIME_BASE_URL/api/health")"
gateway_payload="$(curl --noproxy '*' -fsS "$GATEWAY_BASE_URL/api/health")"
forward_payload="$(curl --noproxy '*' -fsS "$GATEWAY_BASE_URL/api/runtime-orchestrator/health")"

python3 - <<'PY' "$runtime_payload" "$gateway_payload" "$forward_payload"
import json
import sys

runtime_payload = json.loads(sys.argv[1])
gateway_payload = json.loads(sys.argv[2])
forward_payload = json.loads(sys.argv[3])

if runtime_payload.get("status") != "ok":
    raise SystemExit("FIXED_CHAIN_RUNTIME_HEALTH=FAIL")
if gateway_payload.get("status") != "ok":
    raise SystemExit("FIXED_CHAIN_GATEWAY_HEALTH=FAIL")
if forward_payload.get("status") != "ok":
    raise SystemExit("FIXED_CHAIN_FORWARD_HEALTH=FAIL")

print("FIXED_CHAIN_RUNTIME_HEALTH=PASS")
print("FIXED_CHAIN_GATEWAY_HEALTH=PASS")
print("FIXED_CHAIN_FORWARD_HEALTH=PASS")
print("SPLIT_FIXED_RUNTIME_CHAIN=PASS")
PY

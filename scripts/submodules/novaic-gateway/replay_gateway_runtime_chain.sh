#!/usr/bin/env bash
set -euo pipefail

GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://127.0.0.1:19999}"

gateway_payload="$(curl --noproxy '*' -fsS "$GATEWAY_BASE_URL/api/health")"

python3 - <<'PY' "$gateway_payload"
import json
import sys

gateway_payload = json.loads(sys.argv[1])

if gateway_payload.get("status") != "ok":
    raise SystemExit("FIXED_CHAIN_GATEWAY_HEALTH=FAIL")

print("FIXED_CHAIN_GATEWAY_HEALTH=PASS")
print("SPLIT_FIXED_GATEWAY_CHAIN=PASS")
PY

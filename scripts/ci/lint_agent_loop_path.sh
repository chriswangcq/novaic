#!/usr/bin/env bash
# Guard the single active Agent loop path: Environment notifications are drained
# by the required standalone subscriber, never by a runtime switch or disabled
# branch.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BAN='subscriber_enabled|SUBSCRIBER_ENABLED|enable-subscriber|NOVAIC_ENABLE_SUBSCRIBER|Subscriber: disabled|dispatch_subscriber disabled'

if rg -n "$BAN" \
  scripts/start.sh \
  novaic-business/main_subscriber.py \
  novaic-business/main_business.py \
  novaic-common/common/config.py \
  novaic-common/common/strict_config.py \
  novaic-common/config/services.json \
  novaic-common/tests; then
  echo "Agent loop switch/disabled subscriber residue found." >&2
  exit 1
fi

if ! rg -q 'main_subscriber.py' scripts/start.sh; then
  echo "scripts/start.sh must start main_subscriber.py as a required service." >&2
  exit 1
fi

echo "AGENT_LOOP_PATH_LINT=PASS"

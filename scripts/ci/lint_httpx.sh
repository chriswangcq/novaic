#!/usr/bin/env bash
set -e
PATTERN='httpx\.(Async)?Client\('
ALLOWLIST=(
  'novaic-common/common/http/clients.py'
  'tests/'
  # TRANSITIONAL — remove line-by-line as PRs migrate:
  'novaic-device/device/gateway_signaling.py'
  'novaic-business/business/provider_client.py'
  'novaic-business/business/agent_actions.py'
  'novaic-business/business/internal/factory_client.py'
  'novaic-business/business/internal/message.py'
  'novaic-business/business/internal/signaling.py'
  'novaic-business/business/factory_admin_client.py'
  'novaic-business/business/device_client.py'
  'novaic-agent-runtime/task_queue/factory_client.py'
  'novaic-agent-runtime/task_queue/utils/cortex_bridge.py'
  'novaic-gateway/gateway/api/app_client.py'
  'novaic-cortex/novaic_cortex/file_resolver.py'
  'novaic-llm-factory/factory/routes/config_routes.py'
  'novaic-llm-factory/factory/providers.py'
)
HITS=$(rg -l "$PATTERN" novaic-*/ || true)
if [ -z "$HITS" ]; then
    echo "httpx lint OK"
    exit 0
fi
for f in $HITS; do
    ok=0
    for a in "${ALLOWLIST[@]}"; do
        [[ "$f" == *"$a"* ]] && ok=1
    done
    [[ $ok -eq 0 ]] && echo "BAN: $f references $PATTERN outside allowlist" && exit 1
done
echo "httpx lint OK"

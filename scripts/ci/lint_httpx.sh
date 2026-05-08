#!/usr/bin/env bash
set -e
PATTERN='httpx\.(Async)?Client\('
ALLOWLIST=(
  'novaic-common/common/http/clients.py'
  'novaic-business/main_subscriber.py'  # PR-34 34d: sync subscriber subprocess entry
  'tests/'
  'novaic-business/business/provider_client.py'  # provider integration boundary
  'novaic-llm-factory/factory/routes/config_routes.py'  # factory config API boundary
  'novaic-llm-factory/factory/providers.py'  # provider integration boundary
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

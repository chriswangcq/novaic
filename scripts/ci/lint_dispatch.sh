#!/usr/bin/env bash
set -e
PATTERN='/api/queue/dispatch'
ALLOWLIST=(
  'novaic-common/common/wake/assembler.py'
  'novaic-agent-runtime/queue_service/main.py'  # 端点定义
  # tests:
  'tests/'
)
HITS=$(rg -l "$PATTERN" novaic-*/ || true)
for f in $HITS; do
    ok=0
    for a in "${ALLOWLIST[@]}"; do
        [[ "$f" == *"$a"* ]] && ok=1
    done
    [[ $ok -eq 0 ]] && echo "BAN: $f references $PATTERN outside allowlist" && exit 1
done
echo "dispatch lint OK"

#!/usr/bin/env bash
set -e
PATTERN='/api/queue/dispatch'
ALLOWLIST=(
  'novaic-common/common/wake/assembler.py'
  'novaic-agent-runtime/queue_service/main.py'  # 端点定义
  # TRANSITIONAL — remove after PR-11/PR-12/PR-13:
  'novaic-business/business/internal/subagent.py'
  'novaic-business/business/message_actions.py'
  'novaic-agent-runtime/task_queue/client.py'
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

#!/bin/bash
# 为卡死的 active runtime 触发 runtime_complete saga
# 用法: ./scripts/trigger_runtime_complete.sh [data_dir] [queue_url]
# 示例: ./scripts/trigger_runtime_complete.sh
#       ./scripts/trigger_runtime_complete.sh ~/Library/Application\ Support/com.novaic.app
#       ./scripts/trigger_runtime_complete.sh ~/.novaic http://127.0.0.1:19997

DATA_DIR="${1:-$HOME/Library/Application Support/com.novaic.app}"
QUEUE_URL="${2:-http://127.0.0.1:19997}"
DB_PATH="$DATA_DIR/runtime_orchestrator.db"

if [[ ! -f "$DB_PATH" ]]; then
  echo "DB not found: $DB_PATH"
  echo "Usage: $0 [data_dir] [queue_url]"
  exit 1
fi

echo "Querying active runtimes from $DB_PATH ..."
ACTIVE=$(sqlite3 "$DB_PATH" "SELECT runtime_id, agent_id, subagent_id FROM agent_runtimes WHERE status='active';")

if [[ -z "$ACTIVE" ]]; then
  echo "No active runtimes found."
  exit 0
fi

echo "Found active runtimes:"
echo "$ACTIVE"
echo ""

while IFS='|' read -r runtime_id agent_id subagent_id; do
  echo "Triggering runtime_complete for $runtime_id (agent=$agent_id, subagent=$subagent_id) ..."
  curl -s -X POST "$QUEUE_URL/api/queue/sagas/start" \
    -H "Content-Type: application/json" \
    -d "{
      \"saga_type\": \"runtime_complete\",
      \"context\": {
        \"runtime_id\": \"$runtime_id\",
        \"agent_id\": \"$agent_id\",
        \"subagent_id\": \"${subagent_id:-main}\"
      },
      \"idempotency_key\": \"runtime-complete-$runtime_id\"
    }"
  echo ""
done <<< "$ACTIVE"

echo "Done. Saga Worker 会认领并执行 runtime_complete。"

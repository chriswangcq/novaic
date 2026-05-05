#!/usr/bin/env bash
# PR-186E — cross-repo guard for the Environment → Runtime → Cortex →
# Activity Timeline main path.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

require_hit() {
  local label="$1"
  shift
  if ! "$@" >/dev/null; then
    echo "[$label] expected main-path marker missing" >&2
    exit 1
  fi
}

forbid_hits() {
  local label="$1"
  shift
  local matches
  matches="$("$@" || true)"
  if [[ -n "$matches" ]]; then
    echo "[$label] retired main-path residue found:" >&2
    echo "$matches" >&2
    exit 1
  fi
}

require_hit "runtime-notification-prompt" \
  rg -q '\[Environment notification\]' novaic-agent-runtime/task_queue/handlers/context_handlers.py
require_hit "runtime-im-read-before-reply" \
  rg -q '_unobserved_current_input_ids' novaic-agent-runtime/task_queue/handlers/environment_tool_handlers.py
require_hit "runtime-scope-end-processed" \
  rg -q 'transition_environment_notifications' novaic-agent-runtime/task_queue/handlers/cortex_handlers.py

require_hit "business-environment-store" \
  rg -q 'environment-notifications' novaic-business/business/environment.py
require_hit "business-environment-api" \
  rg -q '/environment/\{agent_id\}/im/read' novaic-business/business/internal/environment.py

require_hit "runtime-activity-projection" \
  rg -q 'agent-activity-records' novaic-agent-runtime/task_queue/utils/activity_projection.py
require_hit "runtime-activity-phases" \
  rg -q 'phase="reasoning"|phase="observation"|phase="summary"' novaic-agent-runtime/task_queue/utils/activity_projection.py
require_hit "business-activity-entities" \
  rg -q 'agent-activity-records' novaic-business/business/schema_push.py
require_hit "app-activity-timeline" \
  rg -q 'ActivityTimeline' novaic-app/src/components/Chat/ChatPanel.tsx
require_hit "app-activity-entity-cache" \
  rg -q 'agentActivityRecordsStore' novaic-app/src/data/entities/agentActivity.ts

forbid_hits "runtime-old-prompt-or-tools" \
  rg -n 'chat_reply|subagent_report|subagent_query|subagent_cancel|wake_summary|Wake summary|PREV_SCOPE_HISTORY|chat_history' \
    novaic-agent-runtime/task_queue --glob '*.py'

forbid_hits "business-old-loop-source" \
  rg -n 'message_outbox|bulk_transition_messages|stuck-claimed|messages/unread|mark_all_read' \
    novaic-business/business --glob '*.py'

forbid_hits "app-old-monitor-source" \
  rg -n 'ExecutionLog|execution-logs|result_id|_mcp_content' \
    novaic-app/src \
    --glob '*.ts' --glob '*.tsx' \
    --glob '!*.test.ts' --glob '!*.test.tsx'

echo "AGENT_MAIN_PATH_ACCEPTANCE_LINT=PASS"

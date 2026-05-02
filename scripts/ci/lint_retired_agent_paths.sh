#!/usr/bin/env bash
# Guard retired Agent communication / monitor paths from returning to active source.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

failures=0

check_no_hits() {
  local label="$1"
  shift
  local matches
  matches="$("$@" || true)"
  if [[ -n "$matches" ]]; then
    echo "[$label] retired path residue found:" >&2
    echo "$matches" >&2
    failures=1
  fi
}

check_no_hits "app-monitor" \
  find novaic-app/src -type f \
    \( -name '*.ts' -o -name '*.tsx' -o -name '*.json' \) \
    ! -name '*.test.ts' ! -name '*.test.tsx' \
    -exec sh -c 'rg -n "showExecutionLog|show_execution_log|executionLogsStore|from .*/executionLogs|ExecutionLog|useLogs|LogCapsule|MainAgentLogPreview|SubagentList|executionLogUtils|logFormatters|execution-logs" "$@" || true' sh {} +

check_no_hits "cortex-retired-tools" \
  rg -n '"chat_reply"|'\''chat_reply'\''|subagent_report|subagent_query|subagent_cancel|chat_history|wake_summary|Wake summary' \
    novaic-cortex/novaic_cortex --glob '*.py'

check_no_hits "runtime-retired-tools" \
  rg -n '"chat_reply"|'\''chat_reply'\''|subagent_report|subagent_query|subagent_cancel|chat_history|wake_summary|Wake summary' \
    novaic-agent-runtime/task_queue --glob '*.py'

check_no_hits "common-retired-tool-schemas" \
  rg -n '"chat_reply"|'\''chat_reply'\''|subagent_report|subagent_query|subagent_cancel|chat_history' \
    novaic-common/common/tools --glob '*.py'

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

echo "RETIRED_AGENT_PATHS_LINT=PASS"

#!/usr/bin/env bash
# PR-168E — guard the single Environment notification lifecycle model.
#
# Subscriber drains Environment notifications into Queue dispatch. Runtime
# session.init/finalize owns notification claimed/processed transitions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SUBSCRIBER_BAN='scope/append_input|append_scope_input|bulk_transition_messages|/v1/messages/[^[:space:]"'"'"']+/transition|_try_transition_claimed|_try_append_scope_input|subscriber_append_input|subscriber_transition|/v1/outbox|/internal/messages/(bulk-transition|orphaned|stuck-claimed)'

if rg -n --pcre2 "$SUBSCRIBER_BAN" \
  novaic-business/business/subscribers \
  novaic-business/main_subscriber.py; then
  echo "Lifecycle ownership violation: Subscriber must not own Cortex input or message transition writes." >&2
  exit 1
fi

if ! rg -q '_merge_pending_metadata' novaic-agent-runtime/queue_service/session_repo.py; then
  echo "Lifecycle ownership violation: Queue SessionRepository must preserve pending trigger message_ids." >&2
  exit 1
fi

if ! rg -q 'transition_environment_notifications' novaic-agent-runtime/task_queue/handlers/runtime_handlers.py; then
  echo "Lifecycle ownership violation: Runtime session.init must claim Environment notifications." >&2
  exit 1
fi

if rg -n 'bulk_transition_messages|/internal/messages/(bulk-transition|orphaned|stuck-claimed)|/v1/outbox|/v1/orphans|/v1/stuck-claimed' \
  novaic-agent-runtime/task_queue \
  novaic-business/business \
  scripts/start.sh; then
  echo "Lifecycle ownership violation: retired message lifecycle/outbox path found in live code." >&2
  exit 1
fi

"$ROOT/scripts/ci/lint_chat_messages_read.sh"

echo "LIFECYCLE_LOOP_OWNERSHIP_LINT=PASS"

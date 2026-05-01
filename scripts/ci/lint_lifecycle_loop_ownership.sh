#!/usr/bin/env bash
# PR-153C — guard the single lifecycle ownership model.
#
# Subscriber drains message_outbox into Queue and marks outbox delivery.
# It must not write Cortex scope input or claim chat messages directly.
# Queue owns active/pending serialization; Runtime session.init owns
# scope input registration and claimed transitions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SUBSCRIBER_BAN='scope/append_input|append_scope_input|bulk_transition_messages|/v1/messages/[^[:space:]"'"'"']+/transition|_try_transition_claimed|_try_append_scope_input|subscriber_append_input|subscriber_transition'

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

if ! rg -q 'bulk_transition_messages' novaic-agent-runtime/task_queue/handlers/runtime_handlers.py; then
  echo "Lifecycle ownership violation: Runtime session.init must own input message claimed transitions." >&2
  exit 1
fi

"$ROOT/scripts/ci/lint_chat_messages_read.sh"

echo "LIFECYCLE_LOOP_OWNERSHIP_LINT=PASS"

#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# migrate_pr41_agent_reply_orphans.sh
#
# PR-41 (2026-04-21) — one-time cleanup of legacy pending rows in
# chat_messages that HealthWorker's orphan scan (PR-26) + RECOVERED
# re-dispatch (PR-27) would re-wake every 5 minutes forever.
#
# Background
# ----------
# Before PR-41 every chat_messages INSERT was born with
# ``lifecycle='pending'`` regardless of ``type``. But only
# USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT had a registered
# outbox consumer. For every other type (AGENT_REPLY dominantly,
# plus any system notes) no subscriber ever moved the row off
# pending — so orphan-scan flagged them at the 5-min crit threshold
# and re-dispatched them with TriggerType.RECOVERED, which just
# produced another AGENT_REPLY and restarted the loop.
#
# PR-41 two-layer fix (see docs/roadmap/tickets/PR-41-*.md):
#   1. Entangled/packages/server-python/entangled/sql/entity_store.py
#      — non-trigger types are now born ``lifecycle='consumed'``.
#   2. Entangled/packages/server-python/entangled/app/orphans.py
#      — query filters ``type IN (USER_MESSAGE, SUBAGENT_SEND,
#        SPAWN_SUBAGENT)`` so any pre-existing dirt can't escape
#        even if (1) hasn't rolled out yet.
#
# But rows already written in pending state stay there until
# something touches them. This script is that something.
#
# Safety notes
# ------------
# * Scoped by ``type NOT IN (trigger types)`` AND ``lifecycle =
#   'pending'`` — cannot accidentally move a USER_MESSAGE off
#   pending while a dispatch is in flight.
# * Stamps ``lifecycle_updated_at = now_ms`` so PR-31's message
#   trace reflects when the cleanup ran (not when the row was
#   written — misleading).
# * ``claimed_by_scope`` left NULL on purpose; the row never went
#   through claim → consumed, so leaving it NULL advertises
#   "historical, never dispatched" rather than faking ownership.
# * Allowlisted in ``scripts/ci/lint_lifecycle.sh`` (scripts/gateway/
#   prefix) so the raw UPDATE here doesn't trip the lint.
#
# Usage:
#   bash scripts/gateway/migrate_pr41_agent_reply_orphans.sh [DB_PATH]
#
# Default DB_PATH: /opt/novaic/data/gateway.db
# ---------------------------------------------------------------------------
set -euo pipefail

DB_PATH="${1:-/opt/novaic/data/gateway.db}"

if [[ ! -f "$DB_PATH" ]]; then
  echo "ERROR: DB not found at $DB_PATH"
  exit 1
fi

echo "=== Backing up DB ==="
cp "$DB_PATH" "${DB_PATH}.backup_before_pr41_$(date +%Y%m%d_%H%M%S)"

echo "=== Counting affected rows ==="
COUNT=$(sqlite3 "$DB_PATH" "
  SELECT COUNT(*) FROM chat_messages
   WHERE lifecycle = 'pending'
     AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT');
")
echo "Pending non-trigger rows to clean up: $COUNT"

if [[ "$COUNT" -eq 0 ]]; then
  echo "Nothing to migrate. Exiting."
  exit 0
fi

echo "=== Breakdown by type ==="
sqlite3 "$DB_PATH" "
  SELECT type, COUNT(*) FROM chat_messages
   WHERE lifecycle = 'pending'
     AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT')
   GROUP BY type ORDER BY 2 DESC;
"

echo "=== Running migration ==="
NOW_MS=$(($(date +%s) * 1000))
sqlite3 "$DB_PATH" <<SQL
BEGIN TRANSACTION;

UPDATE chat_messages
   SET lifecycle = 'consumed',
       lifecycle_updated_at = ${NOW_MS}
 WHERE lifecycle = 'pending'
   AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT');

COMMIT;
SQL

echo "=== Verifying ==="
REMAINING=$(sqlite3 "$DB_PATH" "
  SELECT COUNT(*) FROM chat_messages
   WHERE lifecycle = 'pending'
     AND type NOT IN ('USER_MESSAGE','SUBAGENT_SEND','SPAWN_SUBAGENT');
")
echo "Remaining pending non-trigger rows: $REMAINING"

if [[ "$REMAINING" -ne 0 ]]; then
  echo "ERROR: migration incomplete, $REMAINING rows still pending"
  exit 1
fi

echo "Migration complete."

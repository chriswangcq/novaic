-- 047 — PR-47 (2026-04-23)
--
-- One-shot cleanup of the 2026-04-17 ~ 2026-04-21 ``USER_MESSAGE``
-- pending pool that PR-41's incomplete fix (pre-amend) left behind.
--
-- Context
-- -------
-- During that window, ``AGENT_REPLY`` rows created via ``_sql_create``
-- retained ``lifecycle='pending'`` and the HealthWorker kept re-
-- dispatching them. The amend closed the producer side, but the
-- already-stale ``USER_MESSAGE`` rows (visible via ``chat_messages
-- lifecycle='pending' AND created_at < now-48h``) still sit on disk and
-- get re-injected into every new Cortex scope via the legacy
-- ``entity_list(read=0)`` assembly (retired by PR-46).
--
-- This script:
--
--   1. Snapshots the victim rows into a backup table so restore is a
--      single ``INSERT OR REPLACE INTO chat_messages SELECT * FROM ...``
--      away (SQLite — O(N) copy; takes <100ms at our scale).
--   2. Flips them to ``lifecycle='consumed'`` with a reason code that
--      the Entangled state-machine reason allow-list whitelists (see
--      ``entangled/sql/message_state.py::_PENDING_CONSUMED_REASON_ALLOWLIST``).
--   3. Leaves ``message_text`` untouched — chat UI must keep rendering
--      the past conversation; only the routing/lifecycle column changes.
--
-- Safety
-- ------
-- * 48h is ~100× larger than the largest plausible legitimate
--   ``pending`` age (seconds-to-minutes). A row that's been pending 48h
--   is unrecoverable by definition: every subscriber tick, every
--   outbox retry, and every HealthWorker scan in that window has
--   already walked past it.
-- * ``AGENT_REPLY`` / ``SKILL_MSG`` / ``TOOL_OUTPUT`` are excluded
--   explicitly — those are non-trigger types and PR-41's amend already
--   stamps them ``consumed`` at birth. Including them here would
--   double-write for no gain; excluding them makes the intent
--   readable in a grep ("this script targets USER_MESSAGE only").
-- * Idempotent: re-running is a no-op. Rows already ``consumed`` won't
--   match the ``WHERE lifecycle='pending'`` filter.
--
-- How to run
-- ----------
--   cp /opt/novaic/data/entangled.db /opt/novaic/data/entangled.db.pr47.bak.$(date +%s)
--   sqlite3 /opt/novaic/data/entangled.db < scripts/migrations/047_cleanup_ancient_user_message_pending.sql
--
-- Observability checklist (paste before / after into the PR comment):
--
--   SELECT type, lifecycle, COUNT(*) FROM chat_messages
--   WHERE created_at < strftime('%s','now','-48 hours') * 1000
--   GROUP BY type, lifecycle;
--
--   -- Post-run expectation: (USER_MESSAGE, pending) row is 0.
--   -- (USER_MESSAGE, consumed) count increases by the same delta.

-- Schema note (confirmed against prod 2026-04-23):
--   chat_messages.created_at  TEXT, default ``datetime('now')``
--                             → ISO-8601 "YYYY-MM-DD HH:MM:SS" (UTC)
--   chat_messages.timestamp   TEXT (client-provided ISO-8601 with tz)
--   chat_messages.lifecycle_updated_at  INTEGER (epoch-millis;
--                             PR-21 state machine writes this as
--                             ``strftime('%s','now')*1000``)
--
-- An early draft of this migration used ``created_at < strftime('%s',
-- 'now','-48 hours') * 1000``. That compares ISO-TEXT against an
-- epoch-millis INTEGER and SQLite silently coerces both to numeric
-- 0/0 — which means ``WHERE`` returns zero rows and the migration
-- appears to succeed while doing nothing. Fixed to use ISO-TEXT on
-- both sides so SQLite's lexicographic comparison works (ISO-8601
-- is lexicographically sortable by design).

BEGIN;

-- Backup table: snapshots the full row, so restore is trivial. The
-- ``IF NOT EXISTS`` makes re-runs safe; second run simply leaves the
-- first run's snapshot in place.
CREATE TABLE IF NOT EXISTS chat_messages_backup_pr47 AS
  SELECT * FROM chat_messages WHERE 0;

INSERT INTO chat_messages_backup_pr47
SELECT *
FROM chat_messages
WHERE type = 'USER_MESSAGE'
  AND lifecycle = 'pending'
  AND created_at < datetime('now', '-48 hours');

-- The flip. ``lifecycle_updated_at`` is bumped so any observability
-- query ordering by recency sees the admin action, not the original
-- pending moment. It stays INTEGER epoch-millis to match PR-21's
-- state machine convention. ``claimed_by_scope`` stays NULL: the
-- row never belonged to any scope, and we don't want to fabricate one.
UPDATE chat_messages
SET lifecycle = 'consumed',
    lifecycle_updated_at = strftime('%s', 'now') * 1000
WHERE type = 'USER_MESSAGE'
  AND lifecycle = 'pending'
  AND created_at < datetime('now', '-48 hours');

-- Observability: one audit row per flipped message so future ops
-- can grep ``message_state_transitions WHERE reason='pr47_...'`` and
-- see exactly which IDs this migration terminated. Schema confirmed
-- against prod 2026-04-23:
--   (id PK autoincr, message_id, from_state, to_state, reason,
--    actor, scope_id, metadata_json, created_at INTEGER epoch-millis)
--
-- ``actor='migration-047'`` marks admin-origin — distinguishes from
-- the runtime's own ``actor='health_worker'`` / ``subscriber`` /
-- ``scope_end`` on regular transitions.
INSERT INTO message_state_transitions (
    message_id, from_state, to_state, reason, actor, scope_id, metadata_json, created_at
)
SELECT
    id,
    'pending',
    'consumed',
    'pr47_ancient_pending_cleanup',
    'migration-047',
    NULL,
    NULL,
    strftime('%s', 'now') * 1000
FROM chat_messages_backup_pr47;

COMMIT;

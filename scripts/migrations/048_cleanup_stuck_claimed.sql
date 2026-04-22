-- 048 — PR-51 (2026-04-23)
--
-- One-shot cleanup of ``chat_messages`` rows stuck at
-- ``lifecycle='claimed'`` with an ancient ``lifecycle_updated_at``.
--
-- Context (see docs/roadmap/tickets/PR-51-stuck-claimed-cleanup.md)
-- ----------------------------------------------------------------
-- Discovered during PR-47 deploy (2026-04-22 18:00 UTC): prod had
-- 28 rows cemented at lifecycle='claimed' across 5 dead scopes.
-- The normal ``claimed → consumed`` edge never fired because the
-- owning Cortex scope died (process restart, PR-48 hadn't been
-- deployed to force rest, pre-PR-41-amend AGENT_REPLYs born
-- ``pending``, etc.). HealthWorker (PR-27) only scans ``pending``,
-- so those rows sit forever.
--
-- Threshold: 24h since ``lifecycle_updated_at``
--   * Normal dispatch → think → consume completes in < 60s.
--   * Even pathologically slow LLM chains < 30m.
--   * 24h is 288× the HealthWorker CRIT threshold (300s / PR-27)
--     and 4× any realistic long-think upper bound.
--   * Narrow enough that a repeat operator run next day catches
--     any new leak before it compounds.
--
-- Schema note — COLUMN TYPE TRAP
-- ------------------------------
--   chat_messages.created_at           TEXT (ISO-8601; default datetime('now'))
--   chat_messages.timestamp            TEXT (ISO-8601 with tz)
--   chat_messages.lifecycle_updated_at INTEGER (epoch-millis; PR-21)
--
-- ``lifecycle_updated_at`` is the column we use here — that's the
-- one the state machine bumps on every transition, including the
-- subscriber-side ``pending → claimed`` flip that set up this rot.
-- It's INTEGER epoch-millis, so the threshold is expressed
-- arithmetically (no ``datetime()`` wrapping).
--
-- PR-47's migration (047_*) hit a variant of this trap: it compared
-- a TEXT ``created_at`` against ``strftime('%s')*1000`` and
-- silently matched zero rows. This script uses INTEGER on both
-- sides; verified locally + on prod.
--
-- Safety
-- ------
-- * Idempotent: re-running is a no-op (``WHERE lifecycle='claimed'``
--   filter excludes already-flipped rows).
-- * The ``claimed → consumed`` edge is a normal allowed transition
--   (PR-21's state machine), NOT gated like PR-47's
--   ``pending → consumed``. No reason-allowlist concern.
-- * Backup table snapshots the full row (id-unique so re-running
--   won't duplicate; INSERT OR IGNORE).
-- * ``message_text``, ``content``, ``metadata`` untouched — the UI
--   keeps rendering past messages.
--
-- How to run
-- ----------
--   cp /opt/novaic/data/entangled.db \
--      /opt/novaic/snapshots/entangled.db.pr51.bak.$(date +%s)
--   sqlite3 /opt/novaic/data/entangled.db \
--      < scripts/migrations/048_cleanup_stuck_claimed.sql
--
-- Observability checklist (paste before / after into PR-51 comment):
--
--   SELECT agent_id, claimed_by_scope, type, COUNT(*)
--   FROM chat_messages
--   WHERE lifecycle = 'claimed'
--   GROUP BY agent_id, claimed_by_scope, type;
--
--   -- Post-run: rows older than 24h are gone from the above list.
--   -- Rows younger than 24h (legitimate in-flight scopes) untouched.

BEGIN;

-- Backup table: snapshots the full row so restore is trivial. The
-- ``IF NOT EXISTS`` makes re-runs safe; the ``INSERT OR IGNORE``
-- (keyed on PK ``id``) means repeat runs won't duplicate if PR-47's
-- backup table already exists and happens to share a row. In
-- practice the sets are disjoint (PR-47 targeted pending,
-- we target claimed) but the guard is cheap.
CREATE TABLE IF NOT EXISTS chat_messages_backup_pr51 AS
  SELECT * FROM chat_messages WHERE 0;

INSERT OR IGNORE INTO chat_messages_backup_pr51
SELECT *
FROM chat_messages
WHERE lifecycle = 'claimed'
  AND lifecycle_updated_at < (strftime('%s', 'now') - 24 * 3600) * 1000;

-- The flip. ``claimed → consumed`` is a normal allowed transition,
-- so no reason-allow-list check fires on the state machine side
-- (confirmed against entangled/sql/message_state.py::ALLOWED_TRANSITIONS).
-- ``lifecycle_updated_at`` is bumped so Grafana / ops queries order
-- by recency see this admin action, not the stale claim moment.
-- ``claimed_by_scope`` is preserved: it's the historical truth that
-- "scope X used to own this row", and leaving it intact helps
-- forensic queries (e.g. "which dead scopes left claims behind").
UPDATE chat_messages
SET lifecycle = 'consumed',
    lifecycle_updated_at = strftime('%s', 'now') * 1000
WHERE lifecycle = 'claimed'
  AND lifecycle_updated_at < (strftime('%s', 'now') - 24 * 3600) * 1000;

-- Audit row per flipped message. Schema (confirmed prod 2026-04-23):
--   (message_id, from_state, to_state, reason, actor, scope_id,
--    metadata_json, created_at INTEGER epoch-millis)
-- ``actor='migration-048'`` keeps this grep-able separately from
-- runtime-origin (``health_worker`` / ``subscriber`` / ``scope_end``).
-- ``scope_id`` carries the DEAD scope that originally claimed the
-- row — useful for the "which ghosts haunted us" forensic query.
INSERT INTO message_state_transitions (
    message_id, from_state, to_state, reason, actor, scope_id, metadata_json, created_at
)
SELECT
    id,
    'claimed',
    'consumed',
    'pr51_stuck_claimed_cleanup',
    'migration-048',
    claimed_by_scope,
    NULL,
    strftime('%s', 'now') * 1000
FROM chat_messages_backup_pr51;

COMMIT;

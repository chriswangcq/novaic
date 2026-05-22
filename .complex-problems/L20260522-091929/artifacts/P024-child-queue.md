# Implement Queue Postgres Cutover

## Problem

Queue still owns the highest-risk active state in `/opt/novaic/data/queue.db`. It should be migrated to the existing `novaic_queue` Postgres database only after preserving task FSM, saga, lease, worker, session, outbox, idempotency, JSON/time, and locking semantics.

## Success Criteria

- Queue has a Postgres-backed production store for all active task, saga, lease, session, outbox, idempotency, and worker state.
- SQLite transaction/busy/locking behavior is preserved with Postgres transactions, row locks, `SKIP LOCKED`, unique constraints, or advisory locks as appropriate.
- Existing Queue SQLite state is backed up and migrated with row-count and semantic invariant checks.
- Queue service and workers are switched to Postgres and health/worker/API smoke checks pass.
- No active Queue writer continues to use `/opt/novaic/data/queue.db` after cutover.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.

# Port Task Idempotency Ledger To Postgres

## Problem Definition

Task idempotency execution guards still use SQLite-shaped SQL and Python-side ISO timestamp parsing around `tq_idempotency_ledger`. In Postgres mode this risks stale lease decisions, JSON double-encoding, owner-token mismatch bugs, and diagnostics row-shape drift. The guard must remain safe because it protects external side effects from duplicate task execution.

## Proposed Solution

Add backend-aware idempotency ledger helpers in `queue_service/queue_db.py`. Keep the sqlite path behavior-compatible, and add a Postgres path that uses transaction-safe row locking or atomic upsert/update statements for acquisition. In Postgres mode, compare `lease_until` with the current timestamptz in SQL rather than parsing ISO strings in Python, bind completed results as JSONB-native values, and normalize diagnostics through row dict/key access so sqlite and Postgres return the same public shape.

The implementation should cover:

- `acquire_idempotency_execution`: missing key/new acquisition, completed reuse, active in-progress duplicate, expired lease reacquire, contention counter updates, and owner-token same-owner renewal behavior.
- `complete_idempotency_execution`: matching in-progress owner/task update, result JSONB binding, and no unsafe overwrite on owner/task mismatch.
- `release_idempotency_execution`: delete only matching in-progress owner/task rows.
- `get_idempotency_diagnostics`: stable ordering and public shape across sqlite tuple rows and Postgres dict-like rows.

## Acceptance Criteria

- Postgres acquisition locks or atomically updates one `idempotency_key` row and preserves completed-result reuse.
- Postgres in-progress lease checks use native timestamptz SQL comparisons, not Python ISO parsing.
- Completion requires matching `owner_token` and `task_id`, and stores completed results as JSONB-compatible values in Postgres mode.
- Release deletes only matching in-progress rows for the same owner/task.
- Diagnostics return the same public field shape for sqlite and Postgres row wrappers.
- Existing sqlite idempotency behavior remains covered by focused regression tests.

## Verification Plan

Add focused fake Postgres tests for generated SQL and bound values covering missing key, new acquisition, active duplicate, expired reacquire, completed duplicate, completion owner mismatch, release, and diagnostics ordering/shape. Run those tests plus selected existing task worker idempotency/retry tests and the current queue Postgres boundary/mutation tests.

## Risks

- A fake Postgres test proves SQL shape and row handling but not all real concurrent contention behavior; staging validation remains later.
- Changing completion upsert semantics can accidentally allow a mismatched worker to overwrite a completed result.
- Diagnostics row normalization can regress existing sqlite tuple-backed tests if not kept small and explicit.

## Assumptions

- P073 already created a Postgres-compatible `tq_idempotency_ledger` table with JSONB result and timestamptz lease fields.
- The real Postgres runtime validation belongs to the later Queue staging validation ticket, not this unit-level repository port.
- Task publish idempotency-key duplicate behavior is handled by P085; this ticket owns execution guard ledger semantics only.

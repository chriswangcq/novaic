# Port Task Mutations And State Locking To Postgres

## Problem Definition

P084 added Postgres task candidate query dialects, but task lifecycle mutations still rely on SQLite-era assumptions: process-local locks, sqlite busy-timeout hints, and reads that are not explicit Postgres row locks. Task publish, complete, fail, heartbeat, release, and cancel must use Postgres-safe task-state locking or compare-and-update semantics so claim, recovery, and worker actions cannot corrupt lifecycle state.

## Proposed Solution

Introduce Postgres mutation helpers in `queue_service/queue_db.py` for reading task state/content with `FOR UPDATE` or a reviewed compare-and-update pattern. Wire complete/fail/heartbeat/release/cancel paths through those helpers for the Postgres backend while preserving existing sqlite fixtures. Ensure publish stores JSONB-compatible values on the Postgres path and keeps idempotency-key behavior. Add focused fake Postgres tests for mutation loser/no-op shapes, result JSON binding, and sqlite compatibility.

## Acceptance Criteria

- Postgres `_get_task_for_update` or equivalent uses `FOR UPDATE` on `tq_task_state` or a documented compare-and-update pattern.
- Postgres complete/fail/heartbeat/release/cancel paths read/lock state before lifecycle decisions and do not depend on process-local locks for correctness.
- Postgres publish path stores task payload/result/dependency values in JSONB-compatible form without breaking sqlite JSON text behavior.
- Postgres mutation paths ignore/remove `sqlite_busy_timeout_ms` correctness assumptions.
- Focused tests cover generated SQL and fake Postgres behavior for complete/fail/heartbeat/release/cancel loser/no-op cases and JSON result binding.
- Existing sqlite task lifecycle tests still pass.

## Verification Plan

Run focused task mutation Postgres tests, selected existing `TaskQueue` sqlite tests, task FSM ledger tests, and query dialect tests. Use static assertions to ensure Postgres mutation SQL contains row locking or compare/update clauses and does not contain SQLite-only busy-timeout assumptions in PG helper paths.

## Risks

- Mutating task lifecycle code can break active queue behavior; keep the change backend-scoped and test sqlite compatibility.
- A fake Postgres test validates SQL shape but not all real lock behavior; real PG validation remains a later staging ticket.
- Publish JSON binding changes must not double-encode JSONB values.

## Assumptions

- P084 provides claim/recovery/cancel candidate SQL helpers.
- P086 will handle the idempotency ledger separately.
- Saga/session/lease ports remain separate children.

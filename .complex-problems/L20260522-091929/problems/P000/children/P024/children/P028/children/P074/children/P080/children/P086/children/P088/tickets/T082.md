# Port Idempotency Completion And Release Ownership To Postgres

## Problem Definition

`complete_idempotency_execution` and `release_idempotency_execution` need backend-aware ownership semantics for the Postgres idempotency ledger. Completion currently serializes results as JSON text and its fallback upsert can overwrite an existing row after the guarded update fails, which is unsafe for mismatched owner-token or task-id cases. Release already carries ownership predicates, but needs explicit coverage under the Postgres port.

## Proposed Solution

Update `complete_idempotency_execution` in `queue_service/queue_db.py` to bind results through `_json_for_backend`, preserving JSON text for sqlite and native JSONB-compatible values for Postgres. Keep the first guarded `UPDATE` requiring `idempotency_key`, `status = 'in_progress'`, `owner_token`, and `task_id`. If no row was updated, insert a completed row only when the key is absent, using `ON CONFLICT(idempotency_key) DO NOTHING`; return whether a row was actually updated or inserted. This prevents mismatched workers from overwriting an existing ledger row.

Keep `release_idempotency_execution` semantically scoped to matching `idempotency_key`, `status = 'in_progress'`, `owner_token`, and `task_id`, and add focused tests that prove the SQL/rowcount behavior for Postgres and sqlite-compatible result binding.

## Acceptance Criteria

- Postgres completion stores native JSONB-compatible result values; sqlite stores JSON text.
- Completion succeeds when the guarded in-progress owner/task row is updated.
- Completion can create a completed row only when the idempotency key is absent.
- Completion returns false and does not overwrite when an existing row belongs to a different owner or task.
- Release deletes only matching in-progress rows and returns false for nonmatching rows.
- Empty idempotency-key behavior remains unchanged for completion and release.

## Verification Plan

Add focused tests for completion result binding, guarded update success, insert-on-missing-key success, conflict/no-overwrite behavior, owner mismatch, task mismatch, release success, release nonmatch, and empty-key behavior. Run these tests with the P087 acquisition tests plus selected idempotency worker policy/retry tests and current Queue Postgres boundary/mutation tests.

## Risks

- Tightening the fallback upsert changes behavior for mismatched completion attempts; this is intended, but worker retry assumptions should be covered by selected idempotency tests.
- SQLite and Postgres both support `ON CONFLICT`, but rowcount behavior should be asserted through fakes and selected sqlite regressions.
- Real concurrent completion contention still belongs to staging validation.

## Assumptions

- P087 has already added `_json_for_backend` and row/result helpers.
- P089 will separately normalize diagnostics row handling.
- Missing-key completion should remain allowed as a completed insert, but existing conflicting rows must not be overwritten.

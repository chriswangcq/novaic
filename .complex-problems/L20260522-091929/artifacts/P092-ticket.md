# Validate Worker Lease Ledger On Postgres Store

## Problem Definition

Worker lease event/state/outbox APIs delegate to the generic FSM store, and P079 already made that store Postgres-aware. P092 still needs explicit lease-level evidence that the adapter passes lease identity, generation, payload, heartbeat, and idempotency data into the Postgres-compatible store correctly, because saga claim/recovery depends on lease ownership state.

## Proposed Solution

Add focused tests for `LeaseLedgerRepository` backed by `FsmSqliteStore` with a fake Postgres DB. Exercise event append, state upsert, outbox append, and duplicate idempotency handling through the actual lease adapter rather than only the generic store. Assert native JSON payload binding, generation values, unique lease identity columns, heartbeat timestamps, transaction requirement behavior, and existing sqlite tests.

## Acceptance Criteria

- Lease event append passes native JSON payload values in Postgres mode and preserves generation/idempotency key.
- Lease state upsert uses `lease_id` as the conflict identity and preserves `machine_type`, `machine_id`, generation, claimed_by, heartbeat_at, and updated_at.
- Lease outbox append passes native JSON payload values and preserves status/idempotency/generation fields.
- Duplicate/idempotent lease event handling returns the existing event id under a Postgres unique violation.
- Existing worker lease ledger sqlite tests remain green.

## Verification Plan

Add `tests/test_queue_postgres_worker_lease_ledger.py` using a fake Postgres DB and the real `LeaseLedgerRepository`. Run it with existing `test_pr313_worker_lease_ledger.py`, generic Postgres FSM store tests, saga query/mutation tests, and selected Queue Postgres boundary tests.

## Risks

- This may be test-only if the generic FSM store already has the required implementation.
- Fake DB tests validate binding and SQL shape, not live Postgres constraints.
- Any discovered generic store gap should be captured as a blocking follow-up instead of patched broadly inside lease-only code.

## Assumptions

- P079 already made `FsmSqliteStore` Postgres-aware for native JSON values, transaction requirements, stable ordering, and unique violation handling.
- P090 and P091 already port saga candidate and mutation behavior that consumes lease state.

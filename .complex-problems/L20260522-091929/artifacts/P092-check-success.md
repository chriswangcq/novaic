# Worker Lease Ledger Verified

## Summary

P092 is successful. Result `R083` adds lease-adapter-level Postgres fake-store evidence for worker lease event, state, outbox, duplicate/idempotent event, and transaction requirement behavior. No production code changes were needed because P079's generic FSM store already supplies the required Postgres behavior.

## Evidence

- `tests/test_queue_postgres_worker_lease_ledger.py` covers `LeaseLedgerRepository` with a fake Postgres DB.
- Event append test proves native JSON payload binding, generation, lease identity, and idempotency key propagation.
- State upsert test proves `ON CONFLICT(lease_id)` unique state semantics and heartbeat/claimed_by/timestamp propagation.
- Outbox append test proves native JSON payload binding, status, attempts, generation, and idempotency values.
- Duplicate event test proves Postgres unique violation fallback returns the existing event id.
- Explicit transaction test proves mutating Postgres store calls require a transaction.
- Verification passed with 5 focused tests and 58 selected worker lease/saga/Queue regression tests.

## Criteria Map

- Worker lease state upserts preserve generation and unique lease identity -> state upsert test.
- Lease event and outbox writes bind JSON values in Postgres-compatible form while sqlite behavior remains intact -> focused event/outbox tests plus existing sqlite worker lease tests.
- Lease recovery queries can rely on native timestamptz values produced by state path -> heartbeat_at and updated_at are passed as native timestamp values through state upsert; P090 recovery consumes native heartbeat comparison.
- Existing worker lease ledger tests remain green -> `test_pr313_worker_lease_ledger.py` passed in selected set.
- Focused tests/audit cover fake-store state writes, event writes, outbox writes, and duplicate/idempotent event handling -> `tests/test_queue_postgres_worker_lease_ledger.py`.

## Execution Map

- T087 / R083 -> added worker lease adapter tests and verification.

## Stress Test

- Failure mode: lease payload is JSON-encoded text in Postgres mode. Covered by native dict parameter assertions.
- Failure mode: lease state uniqueness is not keyed by `lease_id`. Covered by `ON CONFLICT(lease_id)` assertion.
- Failure mode: duplicate lease events throw instead of returning existing id. Covered by unique-violation fallback test.
- Failure mode: Postgres store mutation happens outside an explicit transaction. Covered by transaction requirement test.

## Residual Risk

- Live Postgres lease contention remains a later staging validation problem.

## Result IDs

- R083

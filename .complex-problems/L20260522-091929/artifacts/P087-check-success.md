# Idempotency Acquisition Verified

## Summary

P087 is successful. Result `R076` ports the idempotency acquisition path to backend-aware behavior with Postgres row locking, native timestamptz lease activity checks, JSONB-compatible completed-result reuse, and sqlite compatibility coverage.

## Evidence

- `queue_service/queue_db.py` now has `_idempotency_acquire_select_sql`, whose Postgres form includes `FOR UPDATE` and `lease_until > ?::timestamptz`.
- `acquire_idempotency_execution` uses the backend-specific select SQL and passes `now` into the Postgres lease-active predicate.
- Completed-result reuse uses `_idempotency_result_from_db`, supporting native JSONB values and legacy sqlite JSON strings.
- Active duplicate contention and expired/same-owner reacquire paths are unchanged in public action shape but now derive Postgres lease activity from SQL.
- `tests/test_queue_postgres_idempotency_acquisition.py` covers missing key, missing row insert, completed duplicate, active duplicate contention, expired reacquire, same-owner renewal, sqlite JSON text, and helper SQL shape.
- Verification passed with 10 focused acquisition tests and 53 selected Queue/idempotency regression tests.

## Criteria Map

- Postgres acquisition locks or atomically updates the target row -> Postgres select uses `FOR UPDATE`.
- Completed rows return `completed` with native JSONB result handling -> tested with native dict result and sqlite JSON text.
- Active in-progress rows owned by another token return `in_progress` and increment contention metadata -> covered by fake Postgres test.
- Expired in-progress rows reacquire through native timestamptz comparison -> Postgres SQL contains `lease_until > ?::timestamptz`; expired row test covers reacquire branch.
- Same-owner acquisition behavior remains compatible -> covered by same-owner active lease renewal test.
- Focused tests cover required scenarios and sqlite compatibility -> 10 focused tests passed.

## Execution Map

- T081 / R076 -> implemented backend-aware acquisition SQL, result normalization, row access helper, acquisition wiring, and focused tests.

## Stress Test

- Failure mode: native JSONB dict is treated like a string and fails JSON decoding. Covered by completed duplicate native dict test.
- Failure mode: Postgres branch silently keeps Python ISO lease parsing. Covered by SQL shape assertion for `?::timestamptz` and Postgres command parameter assertions.
- Failure mode: active duplicate does not increment contention metadata. Covered by update SQL/parameter assertions.
- Failure mode: sqlite JSON text compatibility regresses. Covered by sqlite completed duplicate and active duplicate tests.

## Residual Risk

- Fake Postgres tests validate SQL shape and branch behavior, not live concurrent contention; live validation remains a later Queue staging problem.
- Completion/release ownership and diagnostics are separate open children, P088 and P089.

## Result IDs

- R076

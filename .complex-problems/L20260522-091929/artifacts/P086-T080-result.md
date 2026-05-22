# Task Idempotency Ledger Ported Through Children

## Summary

Completed the P086 idempotency ledger port by splitting T080 into three focused child problems and closing each one successfully:

- P087 / R076: acquisition and lease semantics.
- P088 / R077: completion and release ownership semantics.
- P089 / R078: diagnostics row normalization.

Together these cover Postgres row locking or atomic ownership behavior for acquisition, native timestamptz lease checks, JSONB-compatible result handling, owner/task guarded completion and release, and diagnostics compatibility across sqlite tuple rows and Postgres dict-like rows.

## Done

- P087 added Postgres `FOR UPDATE` acquisition, SQL-side `lease_until > ?::timestamptz` lease activity, completed-result normalization, and acquisition tests.
- P088 added backend-aware result binding, safe completion fallback using `ON CONFLICT(idempotency_key) DO NOTHING`, and completion/release tests.
- P089 normalized diagnostics through `_row_value` and preserved public field shape, filter, ordering, and limit clamping.
- Added focused tests:
  - `tests/test_queue_postgres_idempotency_acquisition.py`
  - `tests/test_queue_postgres_idempotency_complete_release.py`
  - `tests/test_queue_postgres_idempotency_diagnostics.py`

## Verification

- P087 focused: 10 passed.
- P088 focused: 8 passed.
- P089 focused: 5 passed.
- Combined selected idempotency/Queue regression set: 66 passed.
- Compileall succeeded for `queue_service/queue_db.py` and the new idempotency test files.
- `git diff --check` succeeded for the touched queue/idempotency files.

## Known Gaps

- Real Postgres runtime/concurrency validation remains a later Queue staging validation problem.

## Child Results

- R076
- R077
- R078

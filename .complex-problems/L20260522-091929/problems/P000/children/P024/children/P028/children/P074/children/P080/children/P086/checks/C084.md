# Task Idempotency Ledger Verified

## Summary

P086 is successful. The split execution closed acquisition, completion/release, and diagnostics through P087, P088, and P089. Together, results `R076`, `R077`, `R078`, and parent result `R079` port the task idempotency ledger to backend-aware Postgres behavior while preserving sqlite compatibility.

## Evidence

- P087 implements Postgres acquisition row locking with `FOR UPDATE`, native `lease_until > ?::timestamptz` lease activity, completed-result reuse, active duplicate contention updates, expired lease reacquire, and same-owner renewal tests.
- P088 implements backend-aware result binding, guarded completion updates requiring matching owner/task, insert-only fallback with `ON CONFLICT DO NOTHING`, no-overwrite conflict behavior, and release ownership tests.
- P089 normalizes diagnostics row handling for tuple and dict-like rows while preserving public field shape, filter, ordering, and limit clamping.
- Combined selected regression verification passed with 66 tests across the new idempotency tests and existing Queue/idempotency suites.

## Criteria Map

- Postgres acquisition locks or atomically updates the target row and preserves completed-result reuse -> P087 / R076.
- In-progress lease checks use native timestamptz comparisons -> P087 / R076.
- Completion requires matching owner token and task id and stores JSONB-compatible results -> P088 / R077.
- Release deletes only matching in-progress owner/task rows -> P088 / R077.
- Diagnostics return the same public shape without tuple-only assumptions -> P089 / R078.
- Focused tests cover missing key, new acquisition, active duplicate, expired reacquire, completed duplicate, completion mismatch/no-overwrite, release, and diagnostics ordering -> P087/P088/P089 test suites, plus 66 selected regressions.

## Execution Map

- T080 split into P087, P088, and P089.
- R076 closed acquisition and lease semantics.
- R077 closed completion and release semantics.
- R078 closed diagnostics normalization.
- R079 records the parent split result.

## Stress Test

- Failure mode: native JSONB values are double-encoded or fail decode. Covered by acquisition and completion native JSON parameter/result tests.
- Failure mode: stale in-progress leases are decided by Python parsing in Postgres mode. Covered by Postgres SQL shape tests for `?::timestamptz`.
- Failure mode: mismatched completion overwrites another owner's ledger row. Covered by guarded predicates and `DO NOTHING` conflict/no-overwrite tests.
- Failure mode: diagnostics break on Postgres dict-like rows. Covered by dict-like row diagnostics tests.

## Residual Risk

- Live Postgres runtime and concurrency behavior still needs the later Queue staging validation problem.

## Result IDs

- R076
- R077
- R078
- R079

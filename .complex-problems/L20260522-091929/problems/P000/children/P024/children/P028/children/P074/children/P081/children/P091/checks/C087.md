# Saga Lifecycle Mutations Verified

## Summary

P091 is successful. Result `R082` adds Postgres saga-state row locking through `_get_saga_for_update`, routes the remaining direct single-saga read paths through that helper, and fixes saga JSON binding/row parsing for Postgres JSONB values while preserving sqlite compatibility.

## Evidence

- `_saga_for_update_sql` includes `FOR UPDATE OF ss` in Postgres mode.
- `_get_saga_for_update` uses the backend-aware helper.
- Heartbeat, mark-launched, append-step-result, check-saga-complete, mark-completed, mark-failed, and cancel-pending no-op tests assert the Postgres lock query is used.
- Saga create binds native context values in Postgres mode and JSON text in sqlite mode.
- `_row_to_dict` preserves native Postgres dict values for `context` and `step_results` while still decoding sqlite JSON text.
- Verification passed with 13 focused saga mutation tests and 72 selected saga/lease/Queue regression tests.

## Criteria Map

- Postgres `_get_saga_for_update` locks `tq_saga_state` -> `_saga_for_update_sql` and no-op mutation tests.
- Lifecycle paths read/lock state before decisions -> focused tests cover heartbeat, launch, append, completion check, completion, fail, and cancel-pending no-op paths.
- Postgres JSON fields bind/preserve native JSONB-compatible values -> create binding and native row parsing tests.
- Existing sqlite saga lifecycle tests remain compatible -> selected saga lifecycle/FSM tests passed.
- Focused tests cover no-op/loser paths, JSONB binding, and lock SQL shape -> 13 focused tests passed.

## Execution Map

- T086 / R082 -> implemented saga lock helper, JSON helpers, wiring, tests, and verification.

## Stress Test

- Failure mode: Postgres native `step_results` dict is discarded by `json.loads` TypeError handling. Covered by native JSONB row parsing test.
- Failure mode: append/check-complete bypass lock helper. Covered by no-op lock clause tests.
- Failure mode: sqlite context binding regresses. Covered by sqlite JSON text create test and selected sqlite saga regressions.

## Residual Risk

- Worker lease ledger Postgres semantics remain P092.
- Live Postgres saga mutation contention remains a later staging validation problem.

## Result IDs

- R082

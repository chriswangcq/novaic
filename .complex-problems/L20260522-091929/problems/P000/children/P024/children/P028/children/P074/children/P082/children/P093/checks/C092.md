# Check: Session State Locking Semantics Succeed

## Summary

`P093` is solved by `R085` plus follow-up `R086`. The implementation adds an explicit Postgres session state locking boundary, wires it into dispatch/attach/finalize/transition paths, and now has behavioral Postgres-mode tests for the race/revalidation cases that the first check found missing.

## Evidence

- `R085` added `FsmSqliteStore.ensure_state_for_update(...)`, `SessionLedgerRepository.ensure_state_locked(...)`, and repository call sites before active-state decisions.
- `R085` verified Postgres SQL shape: insert-if-missing followed by `SELECT ... FOR UPDATE` inside a transaction.
- `R086` added behavioral repository tests for missing-row first dispatch, attach revalidation after active-state change, and finalize restart/no-input-loss.
- Verification evidence includes 66 related session/Postgres tests and compile checks passing.

## Criteria Map

- First dispatch ensures a state row before decisions: satisfied by `ensure_state_for_update(...)` and `test_behavioral_missing_row_dispatch_locks_before_input_and_start_transition`.
- Dispatch/finalize lock state row before decisions: satisfied by repository call sites plus source-order and behavioral tests.
- Attach revalidates active saga/scope/generation under serialization boundary: satisfied by `_record_attach_request_after_transaction` changes and `test_behavioral_attach_revalidation_buffers_when_active_session_changed`.
- Finalize leaves pending inputs restartable: satisfied by `session_ended` locked path and `test_behavioral_finalize_with_pending_input_queues_restart_without_consuming_input`.
- Focused Postgres-path tests cover race/revalidation/no-input-loss behavior: satisfied by `R086`.
- SQLite-specific synchronization remains isolated: store helper keeps SQLite on legacy select shape and no stale session-facing SQLite wording remains in touched business modules.

## Execution Map

- R085 implemented the locking boundary and initial tests.
- R086 closed the behavioral coverage gap from C090.

## Stress Test

- Behavioral tests simulate the plausible failure modes: missing state row on first dispatch, active session changing before attach persistence, and finalize with pending input.
- Store-level tests verify the Postgres row lock SQL used by those paths.

## Residual Risk

- Live multi-connection Postgres stress would add confidence but is no longer blocking for this problem because deterministic Postgres-mode behavior and SQL lock shape are both covered.

## Result IDs

- R085
- R086

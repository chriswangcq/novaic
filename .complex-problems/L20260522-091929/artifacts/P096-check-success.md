# Check: Behavioral Session Locking Coverage Succeeds

## Summary

`R086` closes the gap identified by `C090`: session locking now has behavioral Postgres-mode tests that execute repository paths for missing-row dispatch, attach revalidation, and finalize restart/no-input-loss semantics.

## Evidence

- `tests/test_queue_postgres_session_locking.py` now includes deterministic Postgres-mode fakes and behavioral repository tests.
- The first-dispatch test proves lock-before-append/state-read ordering and verifies the start outbox references the durable input event.
- The attach test proves changed active session state results in buffered input with no attach consumption.
- The finalize test proves pending input is used to queue restart and remains unconsumed.
- Verification ran 66 related tests plus compile checks.

## Criteria Map

- Postgres-mode behavioral tests: satisfied by `FakePostgresTransactionDb` and `BehavioralSessionLedger` executing `SessionRepository` methods.
- Missing-row first dispatch: covered by `test_behavioral_missing_row_dispatch_locks_before_input_and_start_transition`.
- Attach revalidation after active change: covered by `test_behavioral_attach_revalidation_buffers_when_active_session_changed`.
- Finalize pending-input restart/no-input-loss: covered by `test_behavioral_finalize_with_pending_input_queues_restart_without_consuming_input`.
- SQLite isolation: unchanged source-order and store SQL tests still pass; no broad fallback branch added.
- Regression run: 66 tests passed.

## Execution Map

- Result: R086.
- New test coverage lives in `novaic-agent-runtime/tests/test_queue_postgres_session_locking.py`.

## Stress Test

- The tests simulate the plausible races this follow-up targeted: missing initial state row, active session identity changing before attach persistence, and finalize processing with already-pending input.
- Live multi-connection Postgres stress was not required by this follow-up because `P096` explicitly allowed deterministic Postgres spy/fake coverage and `P093/R085` already verifies the store-level `FOR UPDATE` SQL shape.

## Residual Risk

- A live database concurrency test could still add confidence later, but the original `P096` criteria are satisfied without it.

## Result IDs

- R086

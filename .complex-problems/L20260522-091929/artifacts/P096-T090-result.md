# Result: Behavioral Session Locking Coverage Added

## Summary

Added Postgres-mode behavioral tests for the session locking paths that `P093` needed but `R085` did not prove. The tests execute `SessionRepository` methods with deterministic Postgres spy objects and cover missing-row first dispatch, attach revalidation after active-state change, and finalize restart with pending input.

## Done

- Extended `tests/test_queue_postgres_session_locking.py` with `FakePostgresTransactionDb` and `BehavioralSessionLedger`.
- Added a behavioral first-dispatch test proving `ensure_state_locked` occurs before input append/state read and that the start outbox references the durable input event.
- Added a behavioral attach revalidation test proving changed active session state buffers the input and does not consume it as an attach.
- Added a behavioral finalize test proving pending input drives a restart outbox effect and remains unconsumed in the authoritative input ledger.
- Kept the existing SQL-shape and source-order guards from `P093`.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_session_locking.py` -> 8 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_boundary.py tests/test_pr252_session_state_ssot.py tests/test_pr241_pending_inbox_projection.py tests/test_pr269_session_pending_projection_ledger_boundary.py tests/test_pr270_session_finalize_ledger_boundary.py tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr288_session_observed_event_handler.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_saga_query_dialect.py` -> 66 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall -q tests/test_queue_postgres_session_locking.py queue_service/session_repo.py queue_service/session_ledger.py queue_service/fsm/sqlite_store.py` -> passed.

## Known Gaps

- No live Postgres multi-connection stress test was added; this follow-up closes the behavioral repository-path gap with deterministic Postgres-mode fakes, while `P093/R085` already covers the store-level `FOR UPDATE` SQL shape.

## Artifacts

- `novaic-agent-runtime/tests/test_queue_postgres_session_locking.py`

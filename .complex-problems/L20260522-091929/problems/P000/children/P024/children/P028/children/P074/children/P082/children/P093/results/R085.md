# Result: Session State Locking Semantics Ported

## Summary

Implemented an explicit session state serialization boundary for Postgres session decisions. The FSM store can now ensure a missing state row and lock it with `FOR UPDATE`; the session ledger exposes that as `ensure_state_locked`; and the session repository calls it before dispatch, attach revalidation, finalize decisions, and after-transaction session transition writes.

## Done

- Added `FsmSqliteStore.ensure_state_for_update(...)`.
- Postgres path now performs `INSERT ... ON CONFLICT(...) DO NOTHING` followed by `SELECT ... FOR UPDATE` inside an explicit transaction.
- SQLite path keeps the legacy adapter shape and only reads current state through `get_state`.
- Added `SessionLedgerRepository.ensure_state_locked(...)` with a default `no_active` state row shape for first dispatch.
- Updated `SessionRepository.dispatch`, `_record_attach_request_after_transaction`, `session_ended`, `_record_session_transition_after_transaction`, and generation/input helper paths to lock the session state boundary before active-state decisions.
- Removed stale session-facing wording that described the business layer as SQLite-only.
- Added focused tests for the store SQL shape, session ledger delegation, session repo source-order guards, and SQLite adapter isolation.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py tests/test_pr252_session_state_ssot.py tests/test_pr241_pending_inbox_projection.py tests/test_pr270_session_finalize_ledger_boundary.py tests/test_pr273_session_harness_final_residue_guard.py` -> 23 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_boundary.py tests/test_pr252_session_state_ssot.py tests/test_pr241_pending_inbox_projection.py tests/test_pr269_session_pending_projection_ledger_boundary.py tests/test_pr270_session_finalize_ledger_boundary.py tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr288_session_observed_event_handler.py tests/test_pr251_wake_creation_outbox_cutover.py` -> 48 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_boundary.py tests/test_pr252_session_state_ssot.py tests/test_pr241_pending_inbox_projection.py tests/test_pr269_session_pending_projection_ledger_boundary.py tests/test_pr270_session_finalize_ledger_boundary.py tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr288_session_observed_event_handler.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_saga_query_dialect.py` -> 63 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall -q queue_service/session_repo.py queue_service/session_ledger.py queue_service/fsm/sqlite_store.py tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py` -> passed.
- `rg -n "SQLite transaction|Queue Service SQLite|generic FSM SQLite|publish outside the global|_active_session_generation_after_transaction" queue_service/session_repo.py queue_service/session_ledger.py queue_service/fsm/sqlite_store.py tests/test_queue_postgres_session_locking.py` -> no matches.

## Known Gaps

- This ticket uses SQL/adapter tests and source-order guards; it does not run a live multi-connection Postgres race test.
- Parent `P082` still has separate open children for durable outbox drain/retry semantics and session/outbox SQLite runtime residue.

## Artifacts

- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_queue_postgres_fsm_store.py`
- `novaic-agent-runtime/tests/test_queue_postgres_session_locking.py`

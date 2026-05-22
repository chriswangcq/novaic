# Result: Durable Outbox Drains Ported To Postgres Row Claims

## Summary

Implemented Postgres-safe durable outbox drain semantics using transaction-scoped row claims. Generic FSM pending outbox selection now uses `FOR UPDATE SKIP LOCKED` in Postgres and requires an explicit transaction, while session and saga drainers wrap select/publish/ack-or-fail in a dedicated Postgres outbox transaction. SQLite drain behavior remains on its legacy direct path to avoid the local non-reentrant lock manager.

## Done

- Updated `FsmSqliteStore.list_pending_outbox(...)` so Postgres pending selection requires an explicit transaction and appends `FOR UPDATE SKIP LOCKED`.
- Kept SQLite pending outbox selection unchanged and free of Postgres lock syntax.
- Added Postgres tests for deterministic pending ordering, transaction enforcement, row-lock SQL, idempotent publish ack SQL, and retry/dead-letter failure SQL.
- Wrapped `SessionOutboxDispatcher.drain_pending(...)` in a Postgres-only `session_outbox` transaction around select, external publish, and mark-published/failed.
- Wrapped `SagaOrchestrator.drain_pending_effects(...)` in a Postgres-only `saga_outbox` transaction around select, external publish, and mark-published/failed.
- Preserved SQLite drain behavior by bypassing the new outbox transaction wrapper outside Postgres.
- Added source-order guard tests for session and saga outbox drain transaction boundaries.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_outbox_drain_semantics.py` -> 10 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_outbox_drain_semantics.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr326_session_outbox_generic_worker.py` -> 54 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_outbox_drain_semantics.py tests/test_queue_postgres_boundary.py tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_saga_query_dialect.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_worker_lease_ledger.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr311_saga_compensation_outbox_cutover.py` -> 110 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall -q queue_service/fsm/sqlite_store.py queue_service/session_outbox.py queue_service/saga_repo.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_outbox_drain_semantics.py` -> passed.

## Known Gaps

- No live multi-process Postgres drainer stress test was added. The claim SQL and Postgres-only transaction boundaries are covered by focused tests.
- Task and worker-lease outbox ledgers inherit the generic store semantics, but no separate task/lease outbox worker is wired in this slice.

## Artifacts

- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-agent-runtime/queue_service/session_outbox.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/tests/test_queue_postgres_fsm_store.py`
- `novaic-agent-runtime/tests/test_queue_postgres_outbox_drain_semantics.py`

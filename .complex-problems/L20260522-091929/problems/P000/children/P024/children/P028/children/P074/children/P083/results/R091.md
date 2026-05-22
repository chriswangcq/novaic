# Replace Route Transient Error Handling Result

## Summary

Queue route claim/recovery paths now use an explicit transient error classifier instead of route-local SQLite busy handling. Postgres retryable SQLSTATEs are classified into stable `pg_*` reasons, while SQLite busy/locked handling is retained only inside the compatibility classifier branch and tests.

## Done

- Added `queue_service/transient_errors.py` with low-cardinality classification for queue timeouts, Postgres serialization/deadlock/lock/connection/server-unavailable failures, and SQLite busy compatibility.
- Removed direct `sqlite3` import, `sqlite3.OperationalError` catches, route-local SQLite string matching, and hard-coded `reason=sqlite_busy` logging from `queue_service/routes.py`.
- Updated claim/recovery defer paths to preserve empty claim/recovery responses for transient contention and re-raise unknown failures with the original traceback.
- Added classifier/static guard coverage in `tests/test_queue_transient_errors.py`.
- Extended claim/recovery route tests with simulated Postgres transient exceptions and no-`sqlite_busy` log assertions.

## Verification

- `pytest tests/test_queue_transient_errors.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr345_recovery_background_defer.py` passed: 15 tests.
- `pytest tests/test_queue_postgres_boundary.py tests/test_queue_runtime_postgres_default.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_saga_query_dialect.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_outbox_drain_semantics.py` passed: 71 tests.
- `pytest tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr316_taskqueue_state_candidate_cutover.py tests/test_pr314_queue_control_plane_audit_replay.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py` passed: 34 tests.
- Combined focused regression command over the above suites passed: 120 tests.
- `python -m compileall queue_service/routes.py queue_service/transient_errors.py tests/test_queue_transient_errors.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr345_recovery_background_defer.py` passed.

## Known Gaps

- No live Postgres fault-injection test was run; Postgres behavior is covered with simulated SQLSTATE/class-shape exceptions and existing SQL-boundary tests.
- Repository-level transaction calls still carry existing SQLite timeout hints for compatibility; this result only removed misleading SQLite busy handling from production route defer semantics.

## Artifacts

- `novaic-agent-runtime/queue_service/transient_errors.py`
- `novaic-agent-runtime/queue_service/routes.py`
- `novaic-agent-runtime/tests/test_queue_transient_errors.py`
- `novaic-agent-runtime/tests/test_pr344_queue_claim_busy_handling.py`
- `novaic-agent-runtime/tests/test_pr345_recovery_background_defer.py`

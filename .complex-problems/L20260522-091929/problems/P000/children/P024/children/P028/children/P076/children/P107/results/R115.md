# Queue Worker And Outbox Postgres Staging Smoke Result

## Summary

The api host staging Queue Service worker smoke was completed against Postgres mode. During the first attempt, the smoke exposed three worker-path defects: outbox workers still constructed the sqlite `Database` directly, generic worker shutdown was shadowed by a same-named controller attribute, and the Postgres placeholder converter preserved the `LIMIT ? FOR UPDATE SKIP LOCKED` placeholder incorrectly. Those defects were fixed locally, covered by regression tests, deployed to the api staging checkout, and the worker smoke was rerun successfully.

## Done

- Updated session and saga outbox worker assembly to build the Queue database through the shared queue DB boundary, using `NOVAIC_QUEUE_DB_BACKEND=postgres` and the staging DSN file instead of directly creating `data/queue.db`.
- Fixed `GenericWorker` and `ConcurrentGenericWorker` shutdown handling so SIGTERM calls the callable `shutdown()` method instead of a shadowed `ShutdownController` object.
- Fixed Postgres qmark conversion so `LIMIT ? FOR UPDATE SKIP LOCKED` binds the limit parameter correctly while preserving JSONB `?` operators.
- Restarted the api staging Queue Service on `127.0.0.1:19987` with Postgres backend healthy.
- Ran bounded `task-worker`, `saga-worker`, `session-outbox-worker`, and `saga-outbox-worker` processes against the api staging target.
- Saved the full smoke report to `.complex-problems/L20260522-091929/artifacts/queue-worker-postgres-smoke-report.json`.

## Verification

- Local regression suite: `PYTHONPATH=.:../novaic-common python3 -m pytest -q tests/test_queue_postgres_boundary.py tests/test_pr324_generic_worker_loop.py tests/test_pr332_concurrent_generic_worker.py tests/test_pr339_worker_startup_db_retry.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr337_worker_command_registry.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_pr342_generic_fsm_transition_runner.py` passed with `72 passed in 0.22s`.
- Staging smoke run `20260522T172306Z` returned `ok=true`.
- Worker outcomes: task-worker, saga-worker, session-outbox-worker, and saga-outbox-worker all printed startup lines, received bounded shutdown, printed shutdown complete, had return code `0`, were not killed, and had no traceback or error marker.
- DB count deltas: `tq_session_outbox` stayed at `2` rows but histogram moved from `pending=2` to `published=2`; `tq_sagas` moved from `2` to `4`; `tq_saga_events` moved from `7` to `10`; `tq_saga_state` moved from completed/failed only to `completed=1`, `failed=1`, `cancelled=1`, `pending=1`.
- SQLite residue check: before and after smoke, no `*.db`, `*.sqlite`, or `*.sqlite3` files existed under `/opt/novaic/queue-service-staging`; `lsof +D /opt/novaic/queue-service-staging/data` found no `queue.db` or sqlite holders.

## Known Gaps

None for this ticket. The workers were intentionally bounded by the smoke harness, so `timed_out=true` in the JSON report means the harness sent SIGTERM after the startup/drain window; the processes handled that cleanly.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-worker-postgres-smoke-report.json`
- Local source changes: `novaic-agent-runtime/task_queue/workers/assembly_factories.py`, `novaic-agent-runtime/queue_service/worker/generic_worker.py`, `novaic-agent-runtime/queue_service/worker/concurrent_worker.py`, `novaic-agent-runtime/queue_service/db/postgres.py`, plus earlier Postgres JSON/schema fixes in Queue Service modules.

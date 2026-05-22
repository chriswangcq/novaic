# Queue Service API Smoke Result

## Summary

Ran representative Queue Service API smokes against the real api-host staging service at `http://127.0.0.1:19987`. The first smoke attempts uncovered two additional Postgres JSONB binding defects; both were fixed locally, deployed to the staging checkout, and covered by focused tests. The final smoke passed 26 HTTP operations with no skipped operations.

## Done

- Verified `/health` and `/ready` against the running staging service.
- Exercised task APIs:
  - publish, claim, complete, get;
  - publish, claim, terminal fail.
- Exercised idempotency APIs:
  - first acquire -> `acquired`;
  - duplicate acquire while leased -> `in_progress`;
  - complete;
  - acquire after completion -> `completed`.
- Exercised saga APIs:
  - create, claim, launched, complete, get completed saga;
  - create, claim, fail, get failed saga.
- Exercised session APIs:
  - dispatch -> `wake_start_queued`;
  - session-ended -> `restart_pending`;
  - sessions and pending diagnostics.
- Queried post-smoke row counts from the staging Postgres container.
- Fixed Postgres JSONB binding issues found by the smoke:
  - `queue_service/queue_db.py`: bind JSON values as JSON text instead of raw Python dict/list.
  - `queue_service/saga_repo.py`: bind saga JSON values as JSON text.
  - `queue_service/fsm/sqlite_store.py`: bind generic FSM payloads as JSON text for Postgres too.

## Verification

- Focused local tests:
  - `PYTHONPATH=.:../novaic-common python3 -m pytest -q tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_boundary.py tests/test_pr342_generic_fsm_transition_runner.py`
  - Result: `49 passed in 0.14s`.
- Remote staging restart after fixes:
  - pid `3607615`;
  - `/health` healthy with `database_backend=postgres`;
  - `/ready` ok.
- Final API smoke:
  - report file: `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`;
  - `ok=true`;
  - run id `20260522T165950Z-74bc8a64`;
  - operation count `26`;
  - skips `[]`.
- Post-smoke counts:
  - `tq_tasks=2`;
  - `tq_task_state=2`;
  - `tq_sagas=2`;
  - `tq_saga_state=2`;
  - `tq_session_events=6`;
  - `tq_session_state=1`;
  - `tq_session_outbox=2`;
  - `tq_idempotency_ledger=1`.

## Known Gaps

- Code fixes are local and deployed to staging; they still need to be committed and pushed.
- The smoke uses the dedicated staging Queue Service and Postgres container, not production traffic.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`
- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-agent-runtime/tests/test_queue_postgres_task_mutations.py`
- `novaic-agent-runtime/tests/test_queue_postgres_saga_mutations.py`
- `novaic-agent-runtime/tests/test_queue_postgres_idempotency_complete_release.py`
- `novaic-agent-runtime/tests/test_pr342_generic_fsm_transition_runner.py`

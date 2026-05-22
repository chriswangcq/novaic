# Queue Postgres Staging Validation Report

Generated: 2026-05-22 17:33 UTC / 2026-05-23 01:33 Asia/Shanghai

## Decision

Ready for the Queue Postgres production-cutover preparation step within the scope of P076. The staging target is isolated from production, Queue Service starts healthy in Postgres mode, representative API smokes pass, worker and outbox worker processes run against the Postgres configuration, and sqlite queue residue checks are clean.

This is not a blanket production traffic approval. It means the Queue Service Postgres runtime path has enough staging evidence to proceed to the next cutover gate.

## Target Summary

- Host alias: `api.gradievo.com`
- Queue Service smoke URL: `http://127.0.0.1:19987`
- Postgres target: isolated staging database and user names only; credential values and credential-file paths are omitted.
- Postgres container: `novaic-queue-staging-postgres`, health `healthy`
- Queue Service health: `healthy`, `database_backend=postgres`
- Queue Service readiness: `ok`, database/backend checks `postgres`, session state/outbox checks `ok`

## Commands Run

- Created and health-checked an isolated Postgres 16 staging container with local-loopback binding.
- Started Queue Service with `NOVAIC_QUEUE_DB_BACKEND=postgres` and a redacted credential-file configuration.
- Ran the API smoke harness against `http://127.0.0.1:19987`.
- Collected post-API-smoke table counts and state histograms through the staging database connection.
- Ran bounded worker smoke processes:
  - `main_novaic.py task-worker --queue-service-url http://127.0.0.1:19987 --pool control`
  - `main_novaic.py saga-worker --queue-service-url http://127.0.0.1:19987 --max-concurrent 1`
  - `main_novaic.py session-outbox-worker --poll-interval 0.5 --batch-size 10`
  - `main_novaic.py saga-outbox-worker --poll-interval 0.5 --batch-size 10`
- Checked the staging runtime tree for sqlite files and used `lsof` against the staging data directory to confirm no sqlite queue holders.

## API Smoke Evidence

Run: `20260522T165950Z-74bc8a64`

Result: passed, 26 operations.

Covered flows:

- Health and readiness endpoints.
- Task publish, claim, complete, get.
- Task publish, claim, fail.
- Idempotency acquire first, duplicate in-progress, complete, completed-result replay.
- Saga create, claim, launched, complete, get.
- Saga create, claim, fail, get.
- Session dispatch, session list, session-ended, pending-input query.

Post-API DB snapshot:

- Schema version: `18`
- `tq_tasks=2`, `tq_task_state=2`, `tq_task_events=6`
- `tq_sagas=2`, `tq_saga_state=2`, `tq_saga_events=7`
- `tq_session_state=1`, `tq_session_events=6`, `tq_session_outbox=2`
- `tq_worker_lease_state=4`, `tq_worker_lease_events=8`
- `tq_idempotency_ledger=1`
- Outbox tables for task, saga, and worker lease were empty.

Post-API state histograms:

- Task state: `done=1`, `failed=1`
- Saga state: `completed=1`, `failed=1`
- Session outbox: `pending=2`
- Session state: `starting=1`

## Worker And Outbox Smoke Evidence

Run: `20260522T172306Z`

Result: passed.

Process outcomes:

- `task-worker`: startup line present, bounded shutdown complete, return code `0`, no traceback, no error marker.
- `saga-worker`: startup line present, bounded shutdown complete, return code `0`, no traceback, no error marker.
- `session-outbox-worker`: startup line present, bounded shutdown complete, return code `0`, no traceback, no error marker.
- `saga-outbox-worker`: startup line present, bounded shutdown complete, return code `0`, no traceback, no error marker.

Worker smoke DB deltas:

- `tq_session_outbox` stayed at 2 rows but moved from `pending=2` to `published=2`.
- `tq_sagas` increased from `2` to `4`.
- `tq_saga_events` increased from `7` to `10`.
- `tq_saga_state` changed from `completed=1, failed=1` to `completed=1, failed=1, cancelled=1, pending=1`.
- Task, task state, task events, worker lease, and idempotency counts stayed stable.

SQLite residue:

- Before worker smoke: no `*.db`, `*.sqlite`, or `*.sqlite3` files in the staging runtime tree.
- After worker smoke: no `*.db`, `*.sqlite`, or `*.sqlite3` files in the staging runtime tree.
- `lsof` holder scan: available and no sqlite queue matches.

## Failures Found And Fixed

- Fresh Postgres schema initialization failed after probing a missing `config` table because the transaction was not rolled back before DDL. Fixed with explicit rollback before initialization continues.
- Queue task/saga/FSM JSON payload bindings passed Python dictionaries to Postgres JSONB parameters in several paths. Fixed by binding JSON text consistently for the Postgres boundary.
- Outbox worker assemblies constructed the sqlite `Database` directly. Fixed so session and saga outbox workers use the shared Queue database factory and Postgres schema initializer in Postgres mode.
- Generic worker shutdown was shadowed by a same-named `ShutdownController` attribute. Fixed by storing the controller behind a private attribute so process signal shutdown can call `shutdown()`.
- Postgres placeholder conversion preserved `LIMIT ? FOR UPDATE SKIP LOCKED` as a literal question mark. Fixed so limit parameters bind correctly while JSONB `?` operators remain intact.

## Redaction Check

This report omits connection strings, credential values, and credential-file paths. Source artifacts that retain operational paths are not copied verbatim into this report.

## Residual Risks

- Worker smokes were bounded staging runs. They prove startup, Queue Service connectivity, outbox drain behavior, shutdown, and no sqlite residue, but they are not a full production workload replay.
- Saga worker ran representative startup and polling against staging; deeper business side effects still need the production cutover gate to use service-specific readiness checks.
- The staging database now contains smoke rows. That is expected and isolated from production.

## Source Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-api-smoke-report.json`
- `.complex-problems/L20260522-091929/artifacts/queue-post-smoke-count-report.json`
- `.complex-problems/L20260522-091929/artifacts/queue-worker-postgres-smoke-report.json`
- `.complex-problems/L20260522-091929/artifacts/P107-result.md`
- `.complex-problems/L20260522-091929/artifacts/P107-check.md`

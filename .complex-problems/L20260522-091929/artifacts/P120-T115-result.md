# Fresh Postgres Schema Init Transaction Result

## Summary

Fixed the Queue Service fresh Postgres initialization bug by rolling back after the initial missing-`config` version probe fails. Added a focused regression test that models the fresh Postgres transaction-abort behavior. Deployed the patched runtime file to the api staging checkout, restarted Queue Service, and verified both health endpoints against the staging Postgres DSN file.

## Done

- Patched `novaic-agent-runtime/queue_service/db/schema.py`.
  - `init_postgres_schema` now calls `conn.rollback()` when the initial `SELECT value FROM config` probe fails.
  - `_existing_postgres_table_names` also rolls back if the catalog read fails before returning an empty set.
- Added regression coverage in `novaic-agent-runtime/tests/test_queue_postgres_boundary.py`.
  - The fake Postgres connection can now simulate a missing `config` relation.
  - The new test proves rollback happens before the first `CREATE TABLE`.
- Synced the patched `schema.py` into `/opt/novaic/queue-service-staging/runtime/queue_service/db/schema.py`.
- Restarted the staging Queue Service process on `127.0.0.1:19987`.

## Verification

- Local focused tests:
  - `PYTHONPATH=.:../novaic-common python3 -m pytest -q tests/test_queue_postgres_boundary.py`
  - Result: `12 passed in 0.10s`.
- Remote staging verification on `api.gradievo.com`:
  - Process pid: `3602792`.
  - Port: `127.0.0.1:19987`.
  - DSN source: `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
  - Schema version: `18`.
  - Public table count: `16`.
  - `/health`: `{"status":"healthy","service":"queue-service","version":"1.0.0","database":"postgres:/opt/novaic/queue-staging-postgres/queue-postgres.dsn","database_backend":"postgres"}`.
  - `/ready`: `status=ok`, `database_backend=postgres`, checks for `database`, `postgres`, `tq_tasks`, `tq_sagas`, `tq_session_state`, `tq_session_outbox`, `session_outbox`, and `session_state` all `ok`.
- Remote log confirms:
  - `Postgres connected and initialized`.
  - `Queue Service Startup complete`.
  - `Ready to accept requests`.

## Known Gaps

- The patched submodule code is local and synced to staging; it still needs to be committed and pushed with the ledger changes when the current closure pass is ready.

## Artifacts

- Code: `novaic-agent-runtime/queue_service/db/schema.py`.
- Test: `novaic-agent-runtime/tests/test_queue_postgres_boundary.py`.
- Remote staging log: `/opt/novaic/queue-service-staging/queue-service.log`.

# Queue Service API Staging Smoke Attempt Result

## Summary

P106 could not start Queue Service or run API smokes because the current environment still has no confirmed non-production Queue Postgres DSN/DSN file. The attempt stopped before service startup or database mutation.

## Done

- Checked the current shell for the runtime inputs needed by Queue Service API smokes.
- Confirmed `NOVAIC_QUEUE_POSTGRES_DSN` and `NOVAIC_QUEUE_POSTGRES_DSN_FILE` are unset.
- Confirmed `NOVAIC_QUEUE_DB_BACKEND` is unset in the shell; Queue Service itself defaults to Postgres, but smoke execution still requires a concrete target DSN.
- Confirmed `NOVAIC_QUEUE_INTERNAL_KEY` is unset; this may be acceptable only if the service is bound safely to loopback with internal-key auth disabled.
- Checked Docker state; Docker API is unavailable at `/var/run/docker.sock`, so no local Docker Postgres staging target can be discovered or reused from this environment.
- Re-confirmed code-level runtime inputs in:
  - `novaic-agent-runtime/queue_service/main.py`
  - `novaic-agent-runtime/main_novaic.py`
  - `novaic-agent-runtime/tests/test_queue_runtime_postgres_default.py`
- Did not start the service, call APIs, initialize schemas, or write data because the target identity is absent.

## Verification

- Current env status:
  - `NOVAIC_QUEUE_DB_BACKEND=unset`
  - `NOVAIC_QUEUE_POSTGRES_DSN=unset`
  - `NOVAIC_QUEUE_POSTGRES_DSN_FILE=unset`
  - `NOVAIC_QUEUE_INTERNAL_KEY=unset`
- Docker check returned: Docker API unavailable at `/var/run/docker.sock`.
- Env-reference check found the service code consumes `NOVAIC_QUEUE_DB_BACKEND`, `NOVAIC_QUEUE_POSTGRES_DSN`, and `NOVAIC_QUEUE_POSTGRES_DSN_FILE`.

## Known Gaps

- Queue Service startup in Postgres mode was not attempted.
- Health/readiness endpoints were not called.
- Task, saga, session, and idempotency API smokes were not run.
- DB counts after smokes were not recorded.
- `novaic-agent-runtime/main_novaic.py` still has a CLI default of `sqlite` for `--db-backend`; this does not override `queue_service/main.py`'s service default, but it is a stale-looking path that should be cleaned or made explicitly test-only in the broader SQLite residue cleanup.

Required prerequisite before this ticket can produce a full smoke result:

```bash
cd /Users/wangchaoqun/new-build-novaic/novaic-agent-runtime
export NOVAIC_QUEUE_DB_BACKEND=postgres
export NOVAIC_QUEUE_POSTGRES_DSN_FILE=/absolute/path/to/non-production-queue-postgres.dsn
```

If internal-key auth should be enabled for the smoke runtime:

```bash
export NOVAIC_QUEUE_INTERNAL_KEY='redacted-non-production-key'
```

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/P106-T105-result.md`
- `.complex-problems/L20260522-091929/artifacts/P105-T104-result.md`
- `.complex-problems/L20260522-091929/artifacts/P105-check-success.md`

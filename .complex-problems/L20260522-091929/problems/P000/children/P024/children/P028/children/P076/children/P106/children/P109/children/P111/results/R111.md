# Queue Service Postgres Startup Split Result

## Summary

`T108` split `P111` into two child problems and both are now closed:

- `P114` cleaned the misleading Queue Service startup default so runtime startup is unambiguously Postgres-first instead of silently validating SQLite.
- `P115` supplied/confirmed a non-production Postgres target, started Queue Service against it on the api host, and verified `/health` plus `/ready`.

## Done

- Closed `P114: Clean Queue Startup Postgres Default`.
  - Result `R104`.
  - Success check `C113`.
- Closed `P115: Start Queue Service With Confirmed Postgres Target`.
  - Initial result `R105`.
  - Follow-up path `P116` through `P120`.
  - Final success check `C124`.
- Live staging Queue Service now runs with:
  - `NOVAIC_QUEUE_DB_BACKEND=postgres`.
  - DSN file `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
  - Loopback bind `127.0.0.1:19987`.
  - Passing `/health` and `/ready`.

## Verification

- `P114` success proves startup defaults/code contract no longer steer Queue Service toward SQLite by default.
- `P115` success proves a confirmed staging Postgres target exists and Queue Service can start against it.
- Final remote evidence from `R110`:
  - Queue Service pid `3602792`.
  - `/health` healthy with `database_backend=postgres`.
  - `/ready` ok with core queue/session checks ok.
  - Postgres schema version `18` and `16` public tables.
- Focused code regression verification from `R110`:
  - `PYTHONPATH=.:../novaic-common python3 -m pytest -q tests/test_queue_postgres_boundary.py`
  - `12 passed in 0.10s`.

## Known Gaps

- The local `novaic-agent-runtime` code fix still needs commit/push.
- Higher-level API smokes are outside `P111` and are expected to continue under the next ledger frontier.

## Artifacts

- `R104`, `C113`: Queue startup default cleanup.
- `R105`, `R106`, `R107`, `R108`, `R109`, `R110`: staging target and service startup path.
- `C124`: final `P115` success check.

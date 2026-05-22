# Restart Production Entangled In Postgres Mode Result

## Summary

T064 stopped the old SQLite-mode Entangled runtime and started a new production Entangled process on `127.0.0.1:19900` with the Postgres backend and file-based secret flags. The runtime process itself is alive, uses the expected file-backed DSN/token arguments, and no live holder of `/opt/novaic/data/entangled.db*` was observed.

The cutover did not reach readiness. Business schema registration failed against the PG-mode Entangled process because a literal `%` in SQL DDL was passed through to psycopg unescaped. Entangled is currently serving health with `0` registered entities and readiness returns `503 not_ready`. Business API/subscriber remain frozen.

## Done

- Stopped the previous SQLite-mode Entangled process from the production port.
- Started Entangled in Postgres mode on `127.0.0.1:19900`.
- Used `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Kept raw DSN and raw service-token values out of process arguments.
- Confirmed `/v1/health` returns HTTP 200 from the PG-mode runtime.
- Confirmed no observed process holds `/opt/novaic/data/entangled.db*`.
- Preserved the Business API/subscriber freeze.
- Recorded the rollback source path from the cutover backup directory.

## Verification

- `pgrep`/process inspection showed the Entangled process running with file-based Postgres secret arguments.
- `ss` showed a single listener on `127.0.0.1:19900`.
- `curl /v1/health` returned HTTP 200 with `entities: 0`.
- `curl /v1/ready` returned HTTP 503 with `status: not_ready`.
- `lsof` against `/opt/novaic/data/entangled.db`, `/opt/novaic/data/entangled.db-wal`, and `/opt/novaic/data/entangled.db-shm` showed no live holders.
- The production log showed schema registration failed with `only '%s', '%b', '%t' are allowed as placeholders`.

## Known Gaps

- `/v1/ready` is still failing because schema registration did not complete.
- The PG runtime currently has `0` registered entities.
- The likely code defect is `PostgresDatabase._convert_placeholders`, which converts `?` to `%s` but does not escape literal `%` characters for psycopg.
- Business API/subscriber are still stopped from the cutover freeze and must remain stopped until the PG runtime is repaired and production smokes run.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-production-postgres-runtime-attempt-report.json`
- `/opt/novaic/logs/entangled-production-postgres.log`
- `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`

# Deploy Repaired Entangled Runtime And Restore Production Readiness Result

## Summary

Deployed the repaired Entangled Postgres adapter to `api.gradievo.com`, restarted production Entangled in Postgres mode on `127.0.0.1:19900`, pushed Business and Device schemas directly to Entangled while Business writers remained frozen, and restored readiness.

Final verification shows Entangled health and readiness both return HTTP 200 with 22 registered entities, process arguments use file-backed secrets with no raw DSN/token values, no process holds `/opt/novaic/data/entangled.db*`, and no Business API/subscriber process is running.

## Done

- Synchronized patched `Entangled/packages/server-python/entangled/sql/database.py` to `/opt/novaic/services/Entangled/packages/server-python/entangled/sql/database.py`.
- Restarted Entangled with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Replaced the previous broken PG-mode process with PID `3566057`.
- Pushed 20 Business-owned schemas to Entangled using the production service token file.
- Pushed 2 Device-owned schemas directly to Entangled, bypassing the frozen Business proxy.
- Confirmed Business API/subscriber remained stopped during the repair.
- Pulled the redacted production readiness repair report into the ledger artifacts.

## Verification

- Remote deployed file inspection confirmed the percent-escape patch is present.
- `/v1/health` returned HTTP 200 with `entities: 22`.
- `/v1/ready` returned HTTP 200 with `status: ready`, `entities: 22`, and `missing: []`.
- Registered entities include the 20 Business schemas plus `devices` and `vm-users`.
- `ss`/process inspection confirmed Entangled is listening on `127.0.0.1:19900`.
- Process inspection confirmed file-backed secret flags and `raw_dsn_or_token_in_args: false`.
- `lsof` showed zero holders for `/opt/novaic/data/entangled.db*`.
- Business freeze check showed zero matching Business API/subscriber processes.
- Production log error tail in the repair report is empty after the repaired restart/schema push.

## Known Gaps

- Business API/subscriber are intentionally still frozen. They should be restarted by the later production smoke/restart step after Entangled cutover verification proceeds.
- The original SQLite database files have not yet been archived/removed by this ticket; that remains assigned to the later residue cleanup step.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-production-readiness-repair-report.json`
- `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-production-readiness-repair-report.json`
- `/opt/novaic/logs/entangled-production-postgres.log`

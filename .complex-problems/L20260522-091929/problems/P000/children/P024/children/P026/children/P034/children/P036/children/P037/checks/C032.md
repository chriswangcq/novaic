# P037 Success Check

## Summary

P037 is solved. `R032` closes the Cortex schema-width repair, migration retry, runtime switch, verification, and active-path SQLite cleanup.

## Evidence

- `R032` records the completed Cortex schema repair and production cutover.
- `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md` contains the detailed cutover evidence.
- Local Cortex tests passed with `15 passed`.
- Remote Cortex py_compile passed after deploying the repaired files.
- The repaired migration completed with matching counts for all five operational tables.
- Postgres type checks show the production-sized generation and stack-depth columns are `bigint`.
- Cortex `/health` and `/ready` passed after restart.
- Process args show Cortex running with `--operational-store-backend postgres`.
- Representative `/v1/scope/history` returned HTTP 200 and `history_backend=postgres`.
- The old active SQLite file had no open holder and was moved out of `/opt/novaic/data/cortex`.
- Remote central and rollback notes were updated.

## Criteria Map

- Cortex Postgres operational schema uses `BIGINT`: satisfied by Postgres type checks for `scope_events.generation`, `scope_projection.generation`, `scope_projection.stack_depth`, and `active_stack_projection.generation`.
- `--replace` recovers from partial incompatible schema: satisfied by the successful rerun after changing `--replace` to drop/recreate target tables.
- Remote migration completes with matching counts: satisfied for `cortex_operational_meta=1`, `scope_events=25`, `scope_projection=26`, `active_stack_projection=5`, and `payload_manifest=90`.
- `/opt/novaic/start.sh` starts Cortex with Postgres flags: satisfied by process args after restart.
- Cortex `/health` and `/ready` pass: satisfied after restart.
- Representative operational read smoke passes: satisfied by `/v1/scope/history` HTTP 200 with `history_backend=postgres`.
- No process holds old SQLite and old SQLite moved out of active path: satisfied by `lsof` no-holder evidence and empty active-path `find` after move.
- Rollback note, central note, and local artifact updated: satisfied.

## Execution Map

- Ticket `T035` was classified as `one_go`.
- Result `R032` records the bounded execution attempt and verification.
- No runtime-spawned child problem was needed.

## Stress Test

- The previous failed migration left an incompatible partial target schema; the repaired `--replace` path explicitly dropped and recreated tables, then loaded and count-checked all rows.
- Startup integration caught a missing deployed `api.py` and a missing `--cortex-api-url` argument before cleanup; both were fixed and verified with py_compile and restart.
- Old SQLite cleanup was delayed until after health, readiness, process-arg, read-path, count, and no-holder checks passed.

## Residual Risk

- Queue and Entangled remain separate SQLite-backed services and are outside P037.
- Cortex still carries the `--operational-sqlite-path` CLI argument for parser compatibility, but runtime backend evidence proves Postgres is active.

## Result IDs

- R032

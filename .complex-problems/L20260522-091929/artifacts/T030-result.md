# Cortex operational Postgres cutover result

## Summary

Cortex operational state has been migrated to Postgres end to end. The code now supports a Postgres operational store, production data was migrated to `novaic_cortex`, Cortex runs with the Postgres backend, and the old active SQLite file is retained only in the rollback archive.

## Done

- P033 implemented the Cortex Postgres operational-store adapter, registry/runtime wiring, migration script, tests, and compile checks.
- P034 completed production preflight, backup, migration, runtime switch, health/readiness/read smoke, and old SQLite active-path cleanup.
- The production schema was repaired to use `BIGINT` for millisecond-scale generation counters.
- The migration script can recover from partial target schemas via drop/recreate `--replace`.
- `/v1/scope/history` reports the actual backend and verified `postgres` after cutover.

## Verification

- P033 success check verified code-level implementation and tests.
- P034 success check verified production backup, migration, runtime switch, API smoke, and cleanup.
- Final production counts in `novaic_cortex`:
  - `cortex_operational_meta=1`
  - `scope_events=25`
  - `scope_projection=26`
  - `active_stack_projection=5`
  - `payload_manifest=90`
- Cortex `/health` and `/ready` passed after restart.
- Representative scope-history read returned HTTP 200 and `history_backend=postgres`.
- No `operational.sqlite3*` files remain under `/opt/novaic/data/cortex`.

## Known Gaps

- None for Cortex operational Postgres cutover.
- Queue and Entangled remain separate pending SQLite-to-Postgres migrations.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md`
- `.complex-problems/L20260522-091929/artifacts/P033-check.md`
- `.complex-problems/L20260522-091929/artifacts/P034-check.md`
- `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/CORTEX_POSTGRES_CUTOVER.md`

# Cortex schema repair and production cutover result

## Summary

The Cortex Postgres schema-width issue was repaired and the production Cortex operational store cutover completed. Cortex now runs with the Postgres operational backend, `novaic_cortex` row counts match the source SQLite counts, representative operational reads succeed, and the old active SQLite file has been moved out of `/opt/novaic/data/cortex`.

## Done

- Patched Cortex Postgres schema so production-sized `generation` and `stack_depth` columns use `BIGINT`.
- Patched the Cortex migration script so `--replace` drops and recreates operational tables before loading rows.
- Deployed the repaired Cortex files to `/opt/novaic/services/novaic-cortex`.
- Deployed the matching `api.py` required by the updated `main_cortex.py`.
- Patched `/opt/novaic/start.sh` with `--cortex-api-url`, `--operational-store-backend postgres`, and the Cortex Postgres DSN file flag.
- Reran the Cortex SQLite-to-Postgres migration successfully.
- Restarted `novaic` and verified Cortex on the Postgres backend.
- Removed the old active-path SQLite file after confirming no process held it open.
- Updated the central SQLite classification note, rollback note, and local cutover artifact.

## Verification

- Local Cortex tests passed: `15 passed`.
- Local py_compile passed for the touched Cortex files.
- Remote py_compile passed for deployed Cortex files.
- Migration counts matched:
  - `cortex_operational_meta=1`
  - `scope_events=25`
  - `scope_projection=26`
  - `active_stack_projection=5`
  - `payload_manifest=90`
- Verified Postgres column types:
  - `scope_events.generation=bigint`
  - `scope_projection.generation=bigint`
  - `scope_projection.stack_depth=bigint`
  - `active_stack_projection.generation=bigint`
- `systemctl is-active novaic` returned `active`.
- Cortex `/health` and `/ready` passed.
- Cortex process args include `--operational-store-backend postgres`.
- Representative `/v1/scope/history` read returned HTTP 200 and `history_backend=postgres`.
- `lsof /opt/novaic/data/cortex/operational.sqlite3` showed no holder before cleanup.
- `find /opt/novaic/data/cortex -maxdepth 1 -name 'operational.sqlite3*'` returned no active-path files after cleanup.

## Known Gaps

- Queue and Entangled still remain on SQLite and are tracked as separate cutover problems.
- Cortex still accepts `--operational-sqlite-path` for parser compatibility, but runtime backend selection is Postgres.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md`
- `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/CORTEX_POSTGRES_CUTOVER.md`
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`
- `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3.removed-from-data-dir`

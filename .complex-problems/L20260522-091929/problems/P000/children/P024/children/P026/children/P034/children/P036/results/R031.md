# Cortex production operational cutover partial result

## Summary

The Cortex production cutover attempt completed the safe preparation steps, but did not complete the database migration or runtime switch. Production Cortex remains on the existing SQLite operational store and is healthy. The migration failed while inserting production rows into the new Postgres tables because several operational generation values exceed the Postgres `INTEGER` range. The next repair must widen the Postgres operational schema to `BIGINT`, make `--replace` recreate incompatible target tables, and then rerun the migration and cutover.

## Done

- Created the production rollback archive under `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z`.
- Backed up `/opt/novaic/data/cortex/operational.sqlite3`, its checksum, source table counts, the current `/opt/novaic/start.sh`, and the pre-cutover Cortex code snapshot.
- Deployed the Cortex Postgres-capable code and migration script to `/opt/novaic/services/novaic-cortex`.
- Verified remote Cortex Python compilation after deployment.
- Started the Postgres migration with `--replace`.
- Confirmed after failure that production Cortex still serves readiness from the existing SQLite-backed process.

## Verification

- Source SQLite counts before the attempted cutover were `cortex_operational_meta=1`, `scope_events=25`, `scope_projection=26`, `active_stack_projection=5`, and `payload_manifest=90`.
- The migration failed before `/opt/novaic/start.sh` was patched and before `systemctl restart novaic`.
- Production `/ready` returned `status=ok` after the failed migration attempt.
- The active Cortex process still includes `--operational-sqlite-path /opt/novaic/data/cortex/operational.sqlite3` and does not include Postgres operational-store flags.
- Production SQLite generation ranges include values such as `scope_events.max(generation)=1779178350325`, `scope_projection.max(generation)=1779178350325`, and `active_stack_projection.max(generation)=1779178350587`, which require `BIGINT` in Postgres.

## Known Gaps

- Cortex is not yet cut over to Postgres.
- The deployed Postgres schema still uses `INTEGER` for some production-sized counters and must be widened.
- The migration script's `--replace` path must drop/recreate target tables so a failed incompatible schema can be repaired cleanly.
- `/opt/novaic/data/cortex/operational.sqlite3` remains active and must not be removed until the repaired migration, runtime switch, readiness checks, and no-open-file checks succeed.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/cortex-production-preflight.md`
- `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/scripts/migrate_cortex_operational_sqlite_to_postgres.py`

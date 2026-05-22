# T019 Result - Gateway and Cortex Postgres Boundary Classification

## Summary

Completed the split execution for P010 by classifying Gateway and Cortex SQLite state boundaries separately, then producing a combined synthesis and updating the central SQLite classification note.

## Child Results

- `R017` / P021: Gateway SQLite boundary classified.
- `R018` / P022: Cortex operational SQLite boundary classified.
- `R019` / P023: Gateway/Cortex synthesis created and central note updated.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/gateway-sqlite-boundary.md`
- `.complex-problems/L20260522-091929/artifacts/cortex-sqlite-boundary.md`
- `.complex-problems/L20260522-091929/artifacts/gateway-cortex-sqlite-boundaries.md`

## Boundary Decisions

Gateway:

- Future Postgres target: `novaic_gateway`.
- Migrate: `users`, `refresh_tokens`, `config`.
- Do not migrate zero-row retired tables unless later code audit finds live writers.
- Keep `/opt/novaic/data/gateway.db` in filesystem backups until Gateway PG cutover and stabilization.

Cortex:

- Future Postgres target: `novaic_cortex`.
- Migrate all five current operational tables: `cortex_operational_meta`, `scope_events`, `scope_projection`, `active_stack_projection`, `payload_manifest`.
- Treat `/opt/novaic/data/cortex/operational.sqlite3` as current durable operational state, not disposable cache.
- Keep the SQLite file in filesystem backups until Cortex PG cutover and stabilization.

## Verification

- Gateway health was verified after documentation update.
- Cortex readiness was verified after documentation update.
- The remote central note `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` includes the append-only Gateway/Cortex boundary update.

## No-Cutover Statement

P010 classified boundaries and updated documentation only. It did not perform Gateway or Cortex Postgres cutover, alter service schemas, change runtime config, restart services, or modify service data.

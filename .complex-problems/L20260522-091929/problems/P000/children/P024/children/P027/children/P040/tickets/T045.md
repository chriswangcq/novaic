# Build Entangled SQLite-To-Postgres Migration And Staging Validation

## Problem Definition

Entangled now has local Postgres-capable storage semantics, but production cannot cut over safely until there is an offline SQLite-to-Postgres migration command and a staging validation path. The tooling must prove that table counts, sync versions, SQLite `rowid` replacement, transition IDs, REST behavior, and WebSocket sync behavior survive migration without exposing database secrets.

## Proposed Solution

1. Build a migration command under `Entangled/packages/server-python/scripts/` that opens the SQLite source read-only, creates/clears a Postgres target, registers schemas, copies active tables, copies SQLite `rowid` into Postgres `entangled_rowid`, migrates support tables, resets identity sequences, and writes a redacted migration report.
2. Add focused tests for migration planning and data-copy semantics using temporary SQLite data and a fake or local Postgres adapter boundary where practical.
3. Add a staging validation script or documented command path that starts Entangled in Postgres mode against the staging/test `novaic_entangled` target and runs REST plus WebSocket sync smoke checks.
4. Run the migration against a non-production/staging target or dry-run target first, then capture a report with source counts, target counts, sync-version equality, transition count/max ID, sequence reset evidence, and smoke-test results.
5. Keep production cutover out of this ticket; `P042` owns the production switch and old SQLite cleanup.

## Acceptance Criteria

- Migration command reads SQLite in read-only mode and imports into a clean Postgres target without printing DSNs or passwords.
- The migration covers all active Entangled inventory tables and support tables needed for current runtime behavior.
- Row counts match between SQLite snapshot and Postgres target for all migrated active tables.
- `entangled_sync_versions` key/value pairs match exactly after migration.
- `subagent_state_transitions` count and max ID match, and the next identity value is reset above migrated max ID.
- Dynamic entity tables copy SQLite `rowid` into Postgres `entangled_rowid` wherever stream/list semantics depend on it.
- Migration report records source counts, target counts, semantic checks, sequence resets, and skipped/ignored tables with reasons.
- Staging Entangled can start in Postgres mode without opening the SQLite database file.
- REST smoke checks pass for representative list/read/write/update/delete paths.
- WebSocket sync smoke checks pass for schema/full/head/delta or an explicit equivalent smoke subset justified by available staging data.
- Full relevant local tests pass.

## Verification Plan

Run focused migration tests, py_compile for new scripts/modules, full Entangled server-python pytest, and a staging/dry-run migration command that produces a redacted report. For staging validation, verify health/readiness, representative REST calls, WebSocket sync behavior, and `lsof`/process checks showing the SQLite file is not opened in Postgres mode.

## Risks

- Real Postgres behavior can differ from SQL-capture unit tests, especially around JSONB, bytea, identity sequences, and transaction rollback.
- A migration that forgets SQLite `rowid` would cause stream pagination duplicate/skip bugs.
- WebSocket smoke tests may need existing auth or live service context; if unavailable, the ticket must record the smallest equivalent staging proof and leave a specific follow-up.
- Accidentally logging DSNs or env files would leak secrets into reports or ledger artifacts.
- Clearing the wrong Postgres target would be destructive; the tool must require an explicit clean-target flag and target database confirmation.

## Assumptions

- `P038` and `P039` Postgres implementation slices are complete and available locally.
- A safe staging/test Postgres target can be created on the API machine or locally without touching production `novaic_entangled`.
- Production writers remain on SQLite until `P042`; this ticket may run staging validation but does not switch production traffic.
- The migration report can include table names, counts, and check statuses, but not secret values or full DSNs.

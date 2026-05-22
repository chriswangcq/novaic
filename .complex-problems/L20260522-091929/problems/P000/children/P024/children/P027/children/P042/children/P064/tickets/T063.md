# Run Final Entangled Production Migration Into Postgres

## Problem Definition

With upstream writers frozen and rollback backups prepared, the production Entangled SQLite source must be imported into `novaic_entangled` using the validated migration tooling. The migration must clean/prep the target safely, preserve all planned table counts and semantic values, and produce a redacted report before any runtime restart occurs.

## Proposed Solution

Use the consistent SQLite backup from `P063` as the final source, run `entangled-migrate-postgres` on the API host with `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`, an explicit production target label/confirmation, and report output under the cutover archive. Allow the migration tool to prepare/clean the target according to its guard, then validate the redacted report for source/target counts, sync-version match, transition max ID/count match, `entangled_rowid` preservation, and sequence reset evidence. Do not restart Entangled in this ticket.

## Acceptance Criteria

- `novaic_entangled` target is confirmed clean/prepared through the migration tool.
- Migration runs from the production SQLite backup/source into Postgres without exposing DSN/password values.
- Source and target row counts match for all planned tables.
- Sync-version values match.
- `subagent_state_transitions` count and max ID match.
- `entangled_rowid` preservation and identity/sequence reset checks pass where applicable.
- Redacted migration report is saved locally under ledger artifacts and remotely under the cutover archive.
- Production Entangled is still SQLite-mode after migration; restart is left to `P065`.

## Verification Plan

Run the migration CLI on the API host using the remote venv and Entangled package. Parse the generated JSON report to extract only redacted counts/check statuses. Query Postgres if needed for a small independent count check. Verify production Entangled process args still show SQLite mode after migration.

## Risks

- A count or semantic mismatch must stop the cutover before restart.
- Target cleanup must be limited to `novaic_entangled`, not staging or other service databases.
- If the migration runs from the live file instead of the consistent backup, frozen-window assumptions must be revalidated.

## Assumptions

- `P063` produced `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled.db.sqlite-backup`.
- `novaic_entangled_dsn` exists and connects as `novaic_entangled`.
- Business writers remain frozen while this ticket runs.

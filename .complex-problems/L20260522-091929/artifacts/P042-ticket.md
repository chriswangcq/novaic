# Execute Entangled Production Postgres Cutover

## Problem Definition

Production Entangled must move from `/opt/novaic/data/entangled.db` to Postgres `novaic_entangled` after tooling, staging, and preflight have passed. The cutover must preserve data and sync semantics, avoid concurrent SQLite writes during final export, restart Entangled in Postgres mode with file-based secrets, verify REST and WebSocket behavior, and only then move the old SQLite files out of the active path.

## Proposed Solution

Execute a controlled cutover in small operational phases: prepare rollback copies and service-token file, stop/freeze upstream writers, take a final SQLite snapshot, run `entangled-migrate-postgres` into the clean `novaic_entangled` target, verify migration report counts/versions/transitions/rowid semantics, restart production Entangled on port `19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`, run health/readiness plus representative REST and WebSocket smokes, confirm no active SQLite file holders remain, archive the old SQLite files only after all checks pass, and write rollback/cleanup notes.

## Acceptance Criteria

- Production SQLite files and current runtime config are backed up before migration.
- Upstream writers that can mutate Entangled are stopped/frozen for the final export window.
- Final migration into `novaic_entangled` completes with matching counts and semantic checks.
- Production Entangled starts in Postgres mode on the existing production port.
- Production process args use secret-file flags rather than raw DSN/token values.
- Health/readiness pass after restart.
- Representative REST read/write smoke passes.
- Representative WebSocket sync smoke passes or records the smallest justified direct protocol equivalent.
- No process holds `/opt/novaic/data/entangled.db*` after successful cutover.
- Old SQLite files are archived only after verification succeeds.
- Rollback note and central SQLite classification note are updated.

## Verification Plan

Use the preflight report as the baseline. Run the migration CLI with output report captured under the ledger artifacts, run production HTTP/WS smokes with redacted output, query Postgres counts/versions after cutover, inspect process args and file holders, and verify old SQLite files are no longer in the active path only after service checks pass.

## Risks

- Stopping/frozen writers may interrupt Business/subscriber flows; restart order must be explicit.
- A migration mismatch must trigger rollback rather than partial cutover.
- Production WebSocket list subscriptions involving BLOB-bearing rows may still require a follow-up fix; cutover smokes should choose representative non-BLOB coverage unless product behavior requires BLOB sync immediately.
- Any secret printed by process args or logs must be treated as residue and remediated.

## Assumptions

- `P041` preflight remains fresh enough for the cutover window.
- `novaic_entangled_dsn` and the staging-validated migration/client tooling are present on the API host.
- The user has authorized moving Entangled production to Postgres as part of the broader all-PG migration.

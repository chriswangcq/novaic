# Run Entangled Production Postgres Cutover Preflight

## Problem Definition

Production Entangled is still running on SQLite. Before switching it to Postgres, capture current runtime/data/dependency/rollback evidence and confirm the API host can safely execute the cutover without exposing secrets or changing the production runtime mode.

## Proposed Solution

Run a read-only preflight on `api.gradievo.com`: capture sanitized Entangled process and health/readiness state, inventory active SQLite files and holders, collect fresh source SQLite counts/sync-version/transition/table evidence, verify `novaic_entangled` Postgres connectivity and DSN secret permissions, confirm the deployed Entangled package imports and the migration CLI is available in the runtime venv, prepare a rollback archive directory, and write a redacted preflight report. Do not restart production Entangled and do not switch production to Postgres during this ticket.

## Acceptance Criteria

- Production Entangled health/readiness/runtime state is captured without printing raw service tokens.
- SQLite source counts and key semantic evidence are captured from `/opt/novaic/data/entangled.db`.
- Current process/file holders for `/opt/novaic/data/entangled.db*` are identified.
- `novaic_entangled` Postgres target connectivity is verified through secret-file based access without exposing DSN/password values.
- Deployed Entangled code can import Postgres/migration modules in the production runtime environment.
- Rollback archive directory is prepared and path recorded.
- The report explicitly confirms production Entangled remains SQLite after preflight.

## Verification Plan

Use SSH read-only shell checks, sanitized process inspection, SQLite read-only queries, `docker exec novaic-postgres psql` or DSN-file based Postgres checks, and Python import/compile checks inside the remote runtime venv. Store only counts, booleans, file modes, paths, and sanitized process facts in a local ledger artifact.

## Risks

- Process args may currently contain legacy raw service-token material; preflight must avoid printing it and record only that unsafe pattern exists if detected.
- SQLite may be actively written during counts; the report should mark counts as a point-in-time cutover preflight snapshot.
- If runtime imports fail, preflight should stop and record a blocker rather than attempting production cutover.

## Assumptions

- Production Entangled remains bound to its current SQLite runtime until a later cutover ticket.
- The Postgres container and `novaic_entangled` database/role already exist from earlier Postgres foundation work.
- The migration/staging code validated in `P040` has been synced or can be verified on the API host before cutover.

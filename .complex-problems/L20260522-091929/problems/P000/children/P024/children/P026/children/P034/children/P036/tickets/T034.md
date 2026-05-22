# Execute Cortex Production Operational Cutover

## Problem Definition

Cortex production is ready for operational store cutover from SQLite to Postgres. P035 verified source counts, target DB connectivity, DSN file permissions, dependency readiness, and current readiness.

## Proposed Solution

1. Back up `/opt/novaic/data/cortex/operational.sqlite3`, `start.sh`, and changed Cortex code files.
2. Deploy Cortex Postgres operational store code and migration script.
3. Compile-check deployed Cortex files.
4. Run migration script with `--replace` into `novaic_cortex`.
5. Patch `/opt/novaic/start.sh` to pass:
   - `--operational-store-backend postgres`
   - `--operational-postgres-dsn-file /opt/novaic/postgres/secrets/novaic_cortex_dsn`
6. Restart `novaic`.
7. Verify Cortex `/health`, `/ready`, process args, Postgres row counts, representative operational read, and old SQLite no-holder state.
8. Move old SQLite file out of the active path if safe.
9. Update central classification and rollback notes.

## Acceptance Criteria

- Cortex process starts with Postgres operational backend flags.
- `novaic_cortex` contains matching counts for all five operational tables.
- Cortex `/health` and `/ready` pass.
- Representative operational read smoke passes.
- No active operational SQLite file remains under `/opt/novaic/data/cortex` after safe cleanup.
- Rollback archive and central classification note are updated.

## Verification Plan

- Compare source and target row counts.
- Check process args with secret paths redacted.
- Check Cortex `/health` and `/ready`.
- Check an operational read endpoint or active-stack/status path.
- Check `lsof` and active-path file presence before and after cleanup.

## Risks

- Restarting `novaic` restarts all backend services.
- Control-plane projection mistakes can affect active runtime behavior.
- If the old SQLite file is removed before Postgres is proven healthy, rollback becomes harder.

## Assumptions

- P035 preflight remains valid.
- Workspace files/blob/logical data are out of scope and remain unchanged.

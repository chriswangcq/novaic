# P036 Not Success Check

## Summary

P036 is not solved. `R031` records a safe partial attempt, but the Cortex production operational store is still SQLite-backed and the Postgres migration failed before runtime cutover.

## Blocking Gaps

- Cortex process does not start with Postgres operational backend flags.
- `novaic_cortex` does not yet contain verified matching counts for the five operational tables.
- The migration hit a production data type mismatch because generation values exceed Postgres `INTEGER`.
- `/health`, `/ready`, process-arg, Postgres-count, representative operational-read, and no-SQLite-holder verification have not been completed after a Postgres runtime switch.
- `/opt/novaic/data/cortex/operational.sqlite3` still exists in the active path and remains the active runtime store.
- Rollback and central classification notes are not yet updated for a completed Cortex Postgres cutover.

## Result IDs

- R031

# Cortex production cutover split result

## Summary

The Cortex production operational-store cutover split is complete. P035 verified readiness and P036 completed the production migration, runtime switch, operational read verification, rollback notes, and active-path SQLite cleanup.

## Done

- P035 captured source counts, target DB readiness, DSN permissions, dependency readiness, and current runtime status before cutover.
- P036 backed up the production SQLite operational store and start/code state.
- P036 migrated all five operational tables to `novaic_cortex` with matching counts.
- P036 repaired a discovered schema-width issue via follow-up P037.
- P036 restarted Cortex with the Postgres operational backend.
- P036 verified health, readiness, process args, row counts, and representative operational reads.
- P036 moved old `operational.sqlite3` out of the active path after no-holder verification.
- P036 updated the rollback and central SQLite classification notes.

## Verification

- P035 success check: `C030`.
- P036 final success check after follow-up: `C033`.
- Final cutover artifact: `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md`.
- Remote rollback note: `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/CORTEX_POSTGRES_CUTOVER.md`.

## Known Gaps

- None for Cortex production operational-store cutover.
- Queue and Entangled remain separate pending Postgres cutovers.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/cortex-production-preflight.md`
- `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md`
- `.complex-problems/L20260522-091929/artifacts/P036-check-after-followup.md`
- `.complex-problems/L20260522-091929/artifacts/P037-check.md`

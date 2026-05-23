# Execute Production Queue SQLite To Postgres Migration

## Problem

The verified frozen SQLite backup must be migrated into production Postgres using the approved migration tooling. This belongs under P124 because it is the state-changing data copy step and must happen only after runtime and target preparation pass.

## Success Criteria

- Migration source is the frozen backup `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`, not an active writer path.
- Migration command, code version, source path, target database name, and timestamp are recorded with credentials redacted.
- Migration completes without unresolved errors, warnings, skipped rows, or target conflicts.
- Migration output/report is saved under ledger artifacts.
- If migration fails or reports unresolved warnings, cutover remains blocked and the blocker is recorded.

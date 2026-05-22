# P042: Execute Entangled production Postgres cutover

Status: done
Parent: P027
Root: P000
Source Ticket: T036 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042
Body: problems/P000/children/P024/children/P027/children/P042/README.md
Ticket(s): T061

## Problem
After implementation, staging validation, and preflight, execute the production Entangled cutover from `/opt/novaic/data/entangled.db` to Postgres `novaic_entangled` in a writer-free window, then verify runtime behavior and clean the active SQLite residue.

## Success Criteria
- Production Entangled SQLite files and runtime config are backed up before migration.
- Upstream writers are stopped or frozen before final export.
- Final migration into `novaic_entangled` completes with matching row counts, sync-version values, transition max IDs, and representative semantic checks.
- Entangled starts in Postgres mode with no active SQLite writer.
- Health/readiness, representative REST reads/writes, and WebSocket sync smoke checks pass after restart.
- No process holds `/opt/novaic/data/entangled.db*` after successful cutover.
- Old SQLite files are moved out of the active path only after verification succeeds.
- Rollback note and central SQLite classification note are updated.

## Subproblems
- P063: Prepare Entangled Production Backup And Writer Freeze
- P064: Run Final Entangled SQLite To Postgres Migration
- P065: Restart Production Entangled In Postgres Mode
- P066: Run Entangled Production Postgres REST And WebSocket Smokes
- P067: Archive Entangled SQLite Residue And Update Cutover Notes
- P072: Restart Business Services After Entangled Postgres Cutover

## Results
- R068

## Latest Check
C073

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/README.md
- Ticket T061: problems/P000/children/P024/children/P027/children/P042/tickets/T061.md
- Result R068: problems/P000/children/P024/children/P027/children/P042/results/R068.md
- Check C071: problems/P000/children/P024/children/P027/children/P042/checks/C071.md
- Check C073: problems/P000/children/P024/children/P027/children/P042/checks/C073.md

## Follow-ups
- P072: Restart Business Services After Entangled Postgres Cutover

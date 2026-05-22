# P077: Execute Queue Production Postgres Cutover And Cleanup

Status: todo
Parent: P028
Root: P000
Source Ticket: T072 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077
Body: problems/P000/children/P024/children/P028/children/P077/README.md
Ticket(s): T120

## Problem
After Queue Postgres implementation, migration tooling, and staging validation pass, production Queue must be cut over from `/opt/novaic/data/queue.db` to `novaic_queue` in a controlled window. All queue writers/workers must be stopped or frozen, SQLite backed up, data migrated and verified, Queue service/workers restarted in Postgres mode, smokes passed, and old SQLite residue archived as rollback-only.

## Success Criteria
- All production queue writers/workers using `/opt/novaic/data/queue.db` are identified and stopped/frozen before final backup.
- Final SQLite backup is archived with checksums.
- Migration into `novaic_queue` passes row-count and semantic invariant checks.
- Queue service and worker/outbox processes restart in Postgres mode.
- Health/API/worker/outbox smokes pass.
- No process holds `/opt/novaic/data/queue.db` after cutover.
- Old `queue.db` is archived/rollback-only and central SQLite classification/rollback notes are updated.

## Subproblems
- P121: Commit Push And Deploy Queue Postgres Cutover Code
- P122: Inventory Production Queue Runtime And Cutover Preconditions
- P123: Freeze Queue Writers And Archive Final SQLite Backup
- P124: Migrate Queue SQLite Data To Production Postgres And Verify
- P125: Restart Production Queue Services In Postgres Mode
- P126: Run Production Queue Postgres Health API Worker And Outbox Smokes
- P127: Archive Old Queue SQLite Residue And Update Cleanup Notes

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/README.md
- Ticket T120: problems/P000/children/P024/children/P028/children/P077/tickets/T120.md

## Follow-ups
- none

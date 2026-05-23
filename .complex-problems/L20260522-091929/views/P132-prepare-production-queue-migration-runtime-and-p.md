# P132: Prepare Production Queue Migration Runtime And Postgres Target

Status: done
Parent: P124
Root: P000
Source Ticket: T128 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132
Body: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132/README.md
Ticket(s): T129

## Problem
Before writing Queue data into production Postgres, the production runtime, migration tooling, DSN handling, schema initialization path, and target `novaic_queue` database state must be inspected and prepared. This belongs under P124 because migration execution is unsafe if the code version is stale, the target already has unmanaged rows, or credentials/schema are not handled through the approved redacted paths.

## Success Criteria
- Production Queue runtime checkout and migration tool version are recorded and compatible with the pushed cutover code.
- Production Postgres target connection path is identified without exposing credential values in artifacts.
- Target `novaic_queue` table inventory and row counts are recorded before migration.
- Target state is either proven safe for migration or backed up/cleared through an auditable command path.
- Queue schema initialization is run or verified against production Postgres.
- A redacted preparation report is saved under ledger artifacts.

## Subproblems
- none

## Results
- R125

## Latest Check
C140

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132/README.md
- Ticket T129: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132/tickets/T129.md
- Result R125: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132/results/R125.md
- Check C140: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P132/checks/C140.md

## Follow-ups
- none

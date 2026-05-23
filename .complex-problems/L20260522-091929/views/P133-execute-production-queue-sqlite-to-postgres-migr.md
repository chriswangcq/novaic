# P133: Execute Production Queue SQLite To Postgres Migration

Status: done
Parent: P124
Root: P000
Source Ticket: T128 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133
Body: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133/README.md
Ticket(s): T130

## Problem
The verified frozen SQLite backup must be migrated into production Postgres using the approved migration tooling. This belongs under P124 because it is the state-changing data copy step and must happen only after runtime and target preparation pass.

## Success Criteria
- Migration source is the frozen backup `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`, not an active writer path.
- Migration command, code version, source path, target database name, and timestamp are recorded with credentials redacted.
- Migration completes without unresolved errors, warnings, skipped rows, or target conflicts.
- Migration output/report is saved under ledger artifacts.
- If migration fails or reports unresolved warnings, cutover remains blocked and the blocker is recorded.

## Subproblems
- none

## Results
- R126

## Latest Check
C141

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133/README.md
- Ticket T130: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133/tickets/T130.md
- Result R126: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133/results/R126.md
- Check C141: problems/P000/children/P024/children/P028/children/P077/children/P124/children/P133/checks/C141.md

## Follow-ups
- none

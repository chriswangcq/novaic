# P067: Archive Entangled SQLite Residue And Update Cutover Notes

Status: done
Parent: P042
Root: P000
Source Ticket: T061 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P067
Body: problems/P000/children/P024/children/P027/children/P042/children/P067/README.md
Ticket(s): T069

## Problem
Only after production Postgres runtime and smokes succeed, old active SQLite files should be moved out of the active path and operational notes updated. This belongs under `P042` because leaving active SQLite residue after a successful cutover keeps future ambiguity alive.

## Success Criteria
- `/opt/novaic/data/entangled.db*` files are moved to a timestamped rollback/residue archive after verification succeeds.
- No running process holds the old SQLite files after archival.
- Rollback note records archive path, Postgres runtime facts, and restore steps.
- Central SQLite classification note is updated to mark Entangled SQLite as archived/rollback-only.
- Final report records what was moved, what remains, and why.

## Subproblems
- P071: Persist Entangled Postgres Startup Configuration Before SQLite Archival

## Results
- R067

## Latest Check
C070

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P067/README.md
- Ticket T069: problems/P000/children/P024/children/P027/children/P042/children/P067/tickets/T069.md
- Result R067: problems/P000/children/P024/children/P027/children/P042/children/P067/results/R067.md
- Check C070: problems/P000/children/P024/children/P027/children/P042/children/P067/checks/C070.md

## Follow-ups
- none

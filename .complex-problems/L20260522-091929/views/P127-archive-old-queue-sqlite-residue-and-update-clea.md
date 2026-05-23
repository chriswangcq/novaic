# P127: Archive Old Queue SQLite Residue And Update Cleanup Notes

Status: done
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P127
Body: problems/P000/children/P024/children/P028/children/P077/children/P127/README.md
Ticket(s): T134

## Problem
After production Postgres mode passes smokes, the old SQLite queue file must stop looking like an active runtime path. It should remain available only for rollback until retirement, and central cleanup notes must reflect the new source of truth.

## Success Criteria
- `/opt/novaic/data/queue.db` is moved, renamed, permissioned, or otherwise marked rollback-only according to the rollback plan.
- No production process holds the old SQLite file after cleanup.
- Central SQLite classification and rollback notes are updated to say Queue runtime source of truth is Postgres.
- Cleanup preserves the final backup and checksum.
- The report states whether the rollback-only SQLite artifact can be retired later or must be retained for a defined window.

## Subproblems
- P135: Update Queue Postgres Source-Of-Truth Cleanup Notes

## Results
- R131

## Latest Check
C148

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P127/README.md
- Ticket T134: problems/P000/children/P024/children/P028/children/P077/children/P127/tickets/T134.md
- Result R131: problems/P000/children/P024/children/P028/children/P077/children/P127/results/R131.md
- Check C146: problems/P000/children/P024/children/P028/children/P077/children/P127/checks/C146.md
- Check C148: problems/P000/children/P024/children/P028/children/P077/children/P127/checks/C148.md

## Follow-ups
- P135: Update Queue Postgres Source-Of-Truth Cleanup Notes

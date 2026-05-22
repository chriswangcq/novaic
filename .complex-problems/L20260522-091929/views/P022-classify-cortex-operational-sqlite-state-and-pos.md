# P022: Classify Cortex Operational SQLite State and Postgres Boundary

Status: done
Parent: P010
Root: P000
Source Ticket: T019 (split)
Source Check: none
Package: problems/P000/children/P004/children/P010/children/P022
Body: problems/P000/children/P004/children/P010/children/P022/README.md
Ticket(s): T021

## Problem
Cortex currently references `/opt/novaic/data/cortex/operational.sqlite3`. It may be a durable operational state owner, a rebuildable projection/cache, or a mixed store. The live file, schema, row counts, and code ownership must be classified before deciding whether it should move to `novaic_cortex` or remain a local projection.

This belongs under P010 because Cortex operational storage has different semantics from Gateway auth/ops state.

## Success Criteria
- The live `api` host is checked for `cortex/operational.sqlite3` and any WAL/SHM files, including file metadata and open holders if present.
- Cortex process args and local code paths that reference operational SQLite are identified without recording secrets.
- Cortex schema, indexes, triggers, and row counts are captured if the DB exists.
- Each table group is classified as durable state owner, projection/cache, event log, lock/lease state, or obsolete residue.
- Future Postgres boundary and backup expectations are documented.
- No Cortex production cutover is attempted.

## Subproblems
- none

## Results
- R018

## Latest Check
C018

## Bodies
- Problem: problems/P000/children/P004/children/P010/children/P022/README.md
- Ticket T021: problems/P000/children/P004/children/P010/children/P022/tickets/T021.md
- Result R018: problems/P000/children/P004/children/P010/children/P022/results/R018.md
- Check C018: problems/P000/children/P004/children/P010/children/P022/checks/C018.md

## Follow-ups
- none

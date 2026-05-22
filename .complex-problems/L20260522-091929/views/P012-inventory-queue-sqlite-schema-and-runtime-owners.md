# P012: Inventory Queue SQLite Schema and Runtime Owners

Status: done
Parent: P008
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P004/children/P008/children/P012
Body: problems/P000/children/P004/children/P008/children/P012/README.md
Ticket(s): T009

## Problem
Before mapping queue semantics to Postgres, the current production `queue.db` schema, row counts, indexes, and runtime owners must be captured from evidence. This prevents the migration plan from being based on stale source assumptions.

## Success Criteria
- Production table list, schemas, indexes, triggers, and row counts are captured.
- Queue runtime processes that hold or use `queue.db` are identified.
- Queue code modules that own each table group are mapped.
- A durable inventory artifact exists locally and on the `api` host.
- No production queue data is mutated.

## Subproblems
- none

## Results
- R006

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P004/children/P008/children/P012/README.md
- Ticket T009: problems/P000/children/P004/children/P008/children/P012/tickets/T009.md
- Result R006: problems/P000/children/P004/children/P008/children/P012/results/R006.md
- Check C006: problems/P000/children/P004/children/P008/children/P012/checks/C006.md

## Follow-ups
- none

# P047: Port Entangled stream pagination and cleanup rowid semantics to Postgres

Status: done
Parent: P044
Root: P000
Source Ticket: T040 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047
Body: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047/README.md
Ticket(s): T042

## Problem
Entangled stream/list cleanup paths use SQLite `rowid` as a stable tie-breaker for duplicate cursor values and default cleanup ordering. Port these paths to use Postgres `entangled_rowid`.

## Success Criteria
- Postgres `list_stream` cursor lookup selects `entangled_rowid AS _rid`.
- Postgres before/after pagination predicates compare `entangled_rowid` instead of `rowid`.
- Cleanup/default ordering uses `entangled_rowid DESC` where SQLite uses `rowid DESC`.
- Validation accepts the dialect-specific internal tie-break field safely.
- Tests cover duplicate cursor values and query generation for both SQLite and Postgres.

## Subproblems
- none

## Results
- R038

## Latest Check
C039

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047/README.md
- Ticket T042: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047/tickets/T042.md
- Result R038: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047/results/R038.md
- Check C039: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P047/checks/C039.md

## Follow-ups
- none

# P090: Add Saga Postgres Claim Recovery And JSONB Context Query Dialect

Status: done
Parent: P081
Root: P000
Source Ticket: T084 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090
Body: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090/README.md
Ticket(s): T085

## Problem
Saga claim, stale recovery, and cancel-by-agent candidate queries in `queue_service/saga_repo.py` still use SQLite-flavored ordering, `datetime(...)`, and `json_extract`. The Postgres path needs native timestamptz comparisons, JSONB context predicates, stable ordering, and row locking with `FOR UPDATE SKIP LOCKED` or an equivalent compare/update pattern. This belongs under T084 because candidate selection is the entry point for saga concurrency and stale lease recovery.

## Success Criteria
- Postgres saga claim candidate SQL uses stable ordering and locks selected saga-state rows with `FOR UPDATE ... SKIP LOCKED` or a reviewed compare/update pattern.
- Postgres stale recovery uses native lease heartbeat comparison and locks saga/lease state rows explicitly.
- Postgres cancel-by-agent uses JSONB context predicates instead of `json_extract`.
- SQLite claim/recovery/cancel query behavior remains covered.
- Focused tests assert Postgres SQL shape and absence of SQLite-only `datetime(...)` and `json_extract` in Postgres helpers.

## Subproblems
- none

## Results
- R081

## Latest Check
C086

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090/README.md
- Ticket T085: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090/tickets/T085.md
- Result R081: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090/results/R081.md
- Check C086: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P090/checks/C086.md

## Follow-ups
- none

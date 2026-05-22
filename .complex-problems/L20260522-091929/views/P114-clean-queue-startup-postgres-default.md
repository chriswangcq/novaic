# P114: Clean Queue Startup Postgres Default

Status: done
Parent: P111
Root: P000
Source Ticket: T108 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114/README.md
Ticket(s): T109

## Problem
Queue Service should not have a stale runtime entrypoint that defaults Queue DB startup to SQLite. This child belongs under P111 because a misleading SQLite default can cause local or staging smoke commands to validate the wrong backend before the real service is even started.

## Success Criteria
- Active Queue Service startup entrypoints default `NOVAIC_QUEUE_DB_BACKEND` to `postgres`.
- SQLite remains available only through explicit selection for tests/adapter use.
- Focused tests guard the default and prevent regression to implicit SQLite fallback.
- The change is small and does not rewrite unrelated startup behavior.

## Subproblems
- none

## Results
- R104

## Latest Check
C113

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114/README.md
- Ticket T109: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114/tickets/T109.md
- Result R104: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114/results/R104.md
- Check C113: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P114/checks/C113.md

## Follow-ups
- none

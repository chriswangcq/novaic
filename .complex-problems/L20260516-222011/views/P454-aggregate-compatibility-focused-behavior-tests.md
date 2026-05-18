# P454: Aggregate compatibility focused behavior tests

Status: done
Parent: P406
Root: P000
Source Ticket: T444 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/README.md
Ticket(s): T446

## Problem
Final compatibility verification needs focused behavior tests around attach, finalize, session-ended, recovery, archive, context, shell, and compatibility guards.

## Success Criteria
- Run focused runtime tests for attach/finalize/session-ended/recovery/session-state/generation guards.
- Run focused Cortex tests for archive/context/event/payload/shell compatibility guards.
- Save logs and exit statuses.
- Spawn repair if any suite fails.

## Subproblems
- P456: Runtime focused compatibility behavior tests
- P457: Cortex focused compatibility behavior tests

## Results
- R442

## Latest Check
C468

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/README.md
- Ticket T446: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/tickets/T446.md
- Result R442: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/results/R442.md
- Check C468: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/checks/C468.md

## Follow-ups
- none

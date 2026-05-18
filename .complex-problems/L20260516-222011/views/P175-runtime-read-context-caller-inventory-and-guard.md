# P175: Runtime read_context caller inventory and guard coverage

Status: done
Parent: P162
Root: P000
Source Ticket: T159 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175
Body: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175/README.md
Ticket(s): T162

## Problem
All remaining `read_context` or `context.read` call sites in runtime code/tests must be inventoried and tied to guard coverage, so future changes cannot confuse safe inspection with provider authority.

## Success Criteria
- `rg` inventory of runtime `read_context`, `context.read`, continuity, cross-wake, and historical-context terms is recorded.
- Each active production caller is classified.
- Static or behavioral guard tests for provider non-authority are identified and run.
- Any unclassified production caller is fixed or split.

## Subproblems
- none

## Results
- R157

## Latest Check
C171

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175/README.md
- Ticket T162: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175/tickets/T162.md
- Result R157: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175/results/R157.md
- Check C171: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P175/checks/C171.md

## Follow-ups
- none

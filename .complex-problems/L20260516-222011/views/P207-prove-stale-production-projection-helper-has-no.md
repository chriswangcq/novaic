# P207: Prove stale production projection helper has no live callers

Status: done
Parent: P199
Root: P000
Source Ticket: T195 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207/README.md
Ticket(s): T196

## Problem
Before deleting stale production projection code, verify in-repo callers, exports, tests, and package entry points for `resolve_for_llm` and any helper-only imports. The deletion must be based on current code evidence rather than memory from the inventory.

## Success Criteria
- `resolve_for_llm` caller/export inventory is recorded with exact file references.
- Any remaining external-facing export risk is identified.
- The result clearly states whether deletion can proceed and what must be removed with it.

## Subproblems
- none

## Results
- R191

## Latest Check
C205

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207/README.md
- Ticket T196: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207/tickets/T196.md
- Result R191: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207/results/R191.md
- Check C205: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P207/checks/C205.md

## Follow-ups
- none

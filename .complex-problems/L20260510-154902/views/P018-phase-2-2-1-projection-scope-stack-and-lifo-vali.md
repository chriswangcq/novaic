# P018: Phase 2.2.1: Projection scope stack and LIFO validation

Status: done
Parent: P015
Root: P000
Package: problems/P000/children/P003/children/P015/children/P018
Body: problems/P000/children/P003/children/P015/children/P018/README.md
Ticket(s): T013

## Problem
Implement scope lifecycle state in the pure projector: opening skill scopes, maintaining active stack, parent-child relation, and rejecting close events that violate LIFO. This belongs under P015 because fold rendering depends on correct active-scope state.

## Success Criteria
- `SkillScopeOpened` pushes a skill frame with scope id, parent scope id, skill name, and display name.
- `SkillScopeClosed` closes only the current stack top; non-top close raises projection error.
- Wake frames and skill frames coexist in the stack.
- Tests cover simple open stack, nested open stack, valid close, and LIFO violation.

## Subproblems
- none

## Results
- R010

## Latest Check
C011

## Bodies
- Problem: problems/P000/children/P003/children/P015/children/P018/README.md
- Ticket T013: problems/P000/children/P003/children/P015/children/P018/tickets/T013.md
- Result R010: problems/P000/children/P003/children/P015/children/P018/results/R010.md
- Check C011: problems/P000/children/P003/children/P015/children/P018/checks/C011.md

## Follow-ups
- none

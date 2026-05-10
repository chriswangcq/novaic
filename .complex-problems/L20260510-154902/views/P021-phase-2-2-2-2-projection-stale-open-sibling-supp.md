# P021: Phase 2.2.2.2: Projection stale open sibling suppression

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P003/children/P015/children/P019/children/P021
Body: problems/P000/children/P003/children/P015/children/P019/children/P021/README.md
Ticket(s): T016

## Problem
Implement stale open sibling suppression so that when a newer open sibling appears under the same parent, older still-open sibling output is not projected as active context. This belongs under P019 because stale wake/skill residue was a root cause of earlier DFS context bugs.

## Success Criteria
- Opening a new sibling under the same parent suppresses older open sibling output.
- Older sibling is removed from active stack while the newer sibling remains active.
- Suppression does not break normal nested child scopes.
- Tests cover stale sibling stack and message suppression.

## Subproblems
- none

## Results
- R012

## Latest Check
C013

## Bodies
- Problem: problems/P000/children/P003/children/P015/children/P019/children/P021/README.md
- Ticket T016: problems/P000/children/P003/children/P015/children/P019/children/P021/tickets/T016.md
- Result R012: problems/P000/children/P003/children/P015/children/P019/children/P021/results/R012.md
- Check C013: problems/P000/children/P003/children/P015/children/P019/children/P021/checks/C013.md

## Follow-ups
- none

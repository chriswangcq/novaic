# P004: Upgrade remote Release Controller and verify controller-only deployment

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P004
Body: problems/P000/children/P002/children/P004/README.md
Ticket(s): T004

## Problem
After the controller-only commit is pushed, the API host must run a Release Controller image built from that commit before staging/prod deployment paths are exercised. The final state must prove that backend/factory releases go through the controller, manual deploy paths fail, and polling is enabled.

## Success Criteria
- API host Release Controller image is rebuilt/pushed/deployed from the controller-only commit.
- Staging is deployed through Release Controller and healthy.
- Prod remains in immutable promote/rollback pointer state, promoted to the current release if needed, and healthy.
- Manual backend/factory deploy commands fail locally before remote side effects.
- Release Controller health/status are clean and polling is enabled.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P002/children/P004/README.md
- Ticket T004: problems/P000/children/P002/children/P004/tickets/T004.md
- Result R002: problems/P000/children/P002/children/P004/results/R002.md
- Check C002: problems/P000/children/P002/children/P004/checks/C002.md

## Follow-ups
- none

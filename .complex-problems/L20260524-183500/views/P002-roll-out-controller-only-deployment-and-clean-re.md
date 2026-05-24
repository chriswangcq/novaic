# P002: Roll out controller-only deployment and clean release documentation

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
The code change can temporarily break staging polling if the guarded `deploy` script reaches the API host before the running controller image knows how to pass controller env vars. Documentation also still presents manual deployment commands as acceptable release paths. This child exists to migrate in the right order and verify the final platform shape.

## Success Criteria
- Release Controller runtime is upgraded to code that passes deploy identity before guarded deployments are exercised.
- Staging release and prod promotion/rollback flow are verified through Release Controller APIs or polling.
- Docs describe Release Controller as the only backend/factory release interface and `deploy` as internal executor.
- Manual backend deploy paths are audited after deployment and fail locally before remote side effects.

## Subproblems
- P003: Validate and publish controller-only release commit
- P004: Upgrade remote Release Controller and verify controller-only deployment

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R003: problems/P000/children/P002/results/R003.md
- Check C003: problems/P000/children/P002/checks/C003.md

## Follow-ups
- none

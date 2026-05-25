# P006: Verify production message recovery

Status: todo
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P006
Body: problems/P000/children/P003/children/P006/README.md
Ticket(s): none

## Problem
After deployment, prove the production message pipeline recovered from the stuck Environment notification and no longer fails at the Entangled claim boundary.

## Success Criteria
- Entangled logs no longer show `multiple assignments to same column "updated_at"` for Environment notification claim.
- Subscriber metrics/logs show successful claim or delivery after deployment.
- Queue diagnostics remain healthy and do not show accumulating stuck inputs/sessions.
- Public and internal health checks remain green.
- Any stuck notification evidence is explained: delivered, claimed, or intentionally no longer dispatchable.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P003/children/P006/README.md

## Follow-ups
- none

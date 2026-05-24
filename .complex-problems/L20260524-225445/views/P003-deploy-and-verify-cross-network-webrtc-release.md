# P003: Deploy and verify cross-network WebRTC release

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T004

## Problem
After code/config fixes, the deployed prod/staging stack must actually run the corrected WebRTC path, with host infrastructure and release records matching the immutable release-controller workflow.

## Success Criteria
- Build, commit, and push all code/config changes in the relevant repo and parent repo pointers.
- Use Release Controller, not manual production scripts, to deploy the corrected backend/app-side service artifacts where applicable.
- Verify deployed TURN/registry/gateway configuration from the API host and confirm no stale host-process or manual paths are needed.
- Run local checks plus at least one deployment smoke check that proves ICE/TURN config is served and relay-capable.
- Record the final result in the complex-problems ledger with remaining known manual client-app update steps, if any.

## Subproblems
- P005: Make image release recover from corrupt staging Compose state

## Results
- R003

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T004: problems/P000/children/P003/tickets/T004.md
- Result R003: problems/P000/children/P003/results/R003.md
- Check C004: problems/P000/children/P003/checks/C004.md
- Check C006: problems/P000/children/P003/checks/C006.md

## Follow-ups
- P005: Make image release recover from corrupt staging Compose state

# P004: Deploy and verify TURN credential endpoint

Status: done
Parent: P001
Root: P000
Source Ticket: none (none)
Source Check: C000
Package: problems/P000/children/P001/children/P004
Body: problems/P000/children/P001/children/P004/README.md
Ticket(s): T002

## Problem
The ICE/TURN code path is fixed locally, and the API host has the required `turn_secret`, but prod/staging are still running the old Gateway image where `/api/turn/credentials` is missing. The fixed route must be deployed and verified before ICE/TURN discovery can be considered solved.

## Success Criteria
- Deploy a new API backend image containing the Gateway TURN endpoint and strict TURN config via the Release Controller path.
- Verify prod and staging Gateway instances return authenticated `/api/turn/credentials` responses with at least one `turn:` or `turns:` URL.
- Verify Gateway startup would fail in deployed envs without `turn_secret`, and the current API host secret is present.
- Confirm no WebRTC code path still silently uses STUN-only in deployed cross-network mode.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P001/children/P004/README.md
- Ticket T002: problems/P000/children/P001/children/P004/tickets/T002.md
- Result R001: problems/P000/children/P001/children/P004/results/R001.md
- Check C001: problems/P000/children/P001/children/P004/checks/C001.md

## Follow-ups
- none

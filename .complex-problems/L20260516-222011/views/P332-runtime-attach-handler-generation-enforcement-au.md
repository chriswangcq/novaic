# P332: Runtime attach handler generation enforcement audit

Status: done
Parent: P327
Root: P000
Source Ticket: T319 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332
Body: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332/README.md
Ticket(s): T322

## Problem
Audit the runtime side of active input attachment to verify `expected_session_generation` is required and compared with current wake/session generation before mutating context or inbox.

## Success Criteria
- Locate runtime attach handler and current session generation source.
- Verify missing expected generation is rejected.
- Verify stale expected generation is rejected.
- Identify tests proving handler-side generation enforcement.

## Subproblems
- none

## Results
- R317

## Latest Check
C338

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332/README.md
- Ticket T322: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332/tickets/T322.md
- Result R317: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332/results/R317.md
- Check C338: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P332/checks/C338.md

## Follow-ups
- none

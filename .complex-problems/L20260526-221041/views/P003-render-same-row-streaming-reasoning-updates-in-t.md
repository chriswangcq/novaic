# P003: Render same-row streaming reasoning updates in the App monitor

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T008

## Problem
The App already reads `agent-activity-records` from Entangled, but timeline autoscroll and rendering were built mostly around newly appended rows. Same-row reasoning updates must feel live without introducing a new frontend transport.

## Success Criteria
- Running reasoning rows render with the existing public title contract.
- Same-row text/status updates trigger bottom-follow behavior when the user is near the bottom.
- The App continues to use Entangled cache/query invalidation rather than a new stream channel.
- Tests cover updated timeline projection/render behavior.

## Subproblems
- P010: Update ActivityTimeline for same-record streaming updates
- P011: Verify App Entangled activity contract remains the streaming data path

## Results
- R009

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T008: problems/P000/children/P003/tickets/T008.md
- Result R009: problems/P000/children/P003/results/R009.md
- Check C009: problems/P000/children/P003/checks/C009.md

## Follow-ups
- none

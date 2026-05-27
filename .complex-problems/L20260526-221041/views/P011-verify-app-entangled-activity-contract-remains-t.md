# P011: Verify App Entangled activity contract remains the streaming data path

Status: done
Parent: P003
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P003/children/P011
Body: problems/P000/children/P003/children/P011/README.md
Ticket(s): T010

## Problem
The App must keep using `agent-activity-records` from Entangled for streaming reasoning updates and should not introduce a parallel frontend stream channel.

## Success Criteria
- Activity record entity/type supports `public_title`, `status`, `text`, and timestamps needed for streaming updates.
- No new App websocket/SSE/EventSource path is introduced for reasoning streaming.
- Focused entity contract tests remain green.

## Subproblems
- none

## Results
- R008

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P003/children/P011/README.md
- Ticket T010: problems/P000/children/P003/children/P011/tickets/T010.md
- Result R008: problems/P000/children/P003/children/P011/results/R008.md
- Check C008: problems/P000/children/P003/children/P011/checks/C008.md

## Follow-ups
- none

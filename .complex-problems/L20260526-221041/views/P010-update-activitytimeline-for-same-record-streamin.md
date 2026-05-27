# P010: Update ActivityTimeline for same-record streaming updates

Status: done
Parent: P003
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P003/children/P010
Body: problems/P000/children/P003/children/P010/README.md
Ticket(s): T009

## Problem
`ActivityTimeline` currently follows bottom based mainly on row count/latest key. Streaming reasoning updates mutate the same row's text/status, so the component needs an explicit same-row update key and tests for running reasoning display.

## Success Criteria
- Latest record key includes fields that change during streaming, such as text/status/updated marker.
- Running reasoning rows display `正在思考` and detail text.
- Tests cover public title/projection behavior and same-row update key behavior.

## Subproblems
- none

## Results
- R007

## Latest Check
C007

## Bodies
- Problem: problems/P000/children/P003/children/P010/README.md
- Ticket T009: problems/P000/children/P003/children/P010/tickets/T009.md
- Result R007: problems/P000/children/P003/children/P010/results/R007.md
- Check C007: problems/P000/children/P003/children/P010/checks/C007.md

## Follow-ups
- none

# P003: Cortex display projection must not hide missing media as OK

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Cortex `display_perception` projection currently uses a generic fallback that can produce `{"type":"text","text":"OK"}` when no text or display media is found. For display perception this is too ambiguous: it can hide a broken media projection and make Factory logs look successful while no image was delivered.

## Success Criteria
- `display_perception` projection for empty parsed content returns a diagnostic text marker instead of plain `OK`.
- Normal history/current tool projections can keep their existing text behavior if needed.
- Tests prove empty display projection is distinguishable from a successful image projection.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none

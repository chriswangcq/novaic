# P375: Cortex Archive Diagnostics Persistence Source Map

Status: done
Parent: P373
Root: P000
Source Ticket: T362 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375/README.md
Ticket(s): T363

## Problem
Map the exact Cortex persistence points for `/v1/scope/end` before changing archive diagnostic event shape.

## Success Criteria
- Identify the code that builds `WakeArchived` event payloads.
- Identify where semantic active-stack `remaining_stack` is computed.
- Identify the safest place and shape for explicit runtime diagnostics.
- Confirm which focused tests need to change or be added.

## Subproblems
- none

## Results
- R355

## Latest Check
C378

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375/README.md
- Ticket T363: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375/tickets/T363.md
- Result R355: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375/results/R355.md
- Check C378: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P375/checks/C378.md

## Follow-ups
- none

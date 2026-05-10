# P036: Phase 3.4.2: Wire steps/write to ToolStepRecorded events

Status: done
Parent: P026
Root: P000
Package: problems/P000/children/P004/children/P026/children/P036
Body: problems/P000/children/P004/children/P026/children/P036/README.md
Ticket(s): T032

## Problem
After normalization is explicit, `/v1/steps/write` must append `ToolStepRecorded` events for the active scope.

## Success Criteria
- `steps_write` appends `ToolStepRecorded` with target scope id.
- Event payload preserves call id, tool name, status, observation, and final payload ref.
- Legacy step files remain transitional.
- Focused tests verify event stream rows.

## Subproblems
- none

## Results
- R029

## Latest Check
C031

## Bodies
- Problem: problems/P000/children/P004/children/P026/children/P036/README.md
- Ticket T032: problems/P000/children/P004/children/P026/children/P036/tickets/T032.md
- Result R029: problems/P000/children/P004/children/P026/children/P036/results/R029.md
- Check C031: problems/P000/children/P004/children/P026/children/P036/checks/C031.md

## Follow-ups
- none

# P225: Map runtime step result expansion path

Status: done
Parent: P128
Root: P000
Source Ticket: T216 (split)
Source Check: none
Package: problems/P000/children/P003/children/P128/children/P225
Body: problems/P000/children/P003/children/P128/children/P225/README.md
Ticket(s): T217

## Problem
Runtime LLM preparation must expand `step_ref` tool results through explicit Cortex projections, not by loading raw durable payloads into ordinary history.

## Success Criteria
- File/function path for LLM call preparation and `step_ref` expansion is mapped.
- Projection selection inputs are identified (`round_id`, tool name, tool call id, current/latest status).
- Evidence shows raw durable payloads are not directly inserted by this path.

## Subproblems
- none

## Results
- R214

## Latest Check
C228

## Bodies
- Problem: problems/P000/children/P003/children/P128/children/P225/README.md
- Ticket T217: problems/P000/children/P003/children/P128/children/P225/tickets/T217.md
- Result R214: problems/P000/children/P003/children/P128/children/P225/results/R214.md
- Check C228: problems/P000/children/P003/children/P128/children/P225/checks/C228.md

## Follow-ups
- none

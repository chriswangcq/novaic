# P005: Tool result step_ref projection repair

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P005
Body: problems/P000/children/P002/children/P005/README.md
Ticket(s): T004

## Problem
Cortex event projection stores `ToolStepRecorded.payload_ref` only inside `_metadata.payload_ref`, but runtime LLM expansion requires a top-level `step_ref` on every tool message. This makes the next `react_think` fail before the LLM call.

## Success Criteria
- Projected tool messages include top-level `step_ref` equal to the event `payload_ref` when present.
- Existing metadata payload refs remain available for diagnostics.
- Regression tests prove normal, multiple, and orphan tool-result projections satisfy the runtime step-ref contract.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P002/children/P005/README.md
- Ticket T004: problems/P000/children/P002/children/P005/tickets/T004.md
- Result R002: problems/P000/children/P002/children/P005/results/R002.md
- Check C002: problems/P000/children/P002/children/P005/checks/C002.md

## Follow-ups
- none

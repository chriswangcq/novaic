# P148: write_step_projection call-site boundary audit

Status: done
Parent: P142
Root: P000
Source Ticket: T129 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/README.md
Ticket(s): T133

## Problem
`write_step_projection` connects API/runtime tool observations to workspace step files. Even if lower-level workspace functions are correct, active call sites can still pass legacy inline shapes, skip payload externalization, or write projections without complete refs.

This child belongs under `P142` because the active wiring must prove new execution paths actually use the step normalization/index contract, not merely define it.

## Success Criteria
- Source pointers map all active `write_step_projection` call sites.
- Evidence proves call sites pass structured observation/percept data instead of raw inline result strings.
- Evidence proves call sites propagate `step_ref`/`payload_ref` and artifact metadata into the workspace layer.
- Tests cover at least one active projection path from tool result to step file/index row.

## Subproblems
- P149: Cortex API step projection boundary audit
- P150: Runtime bridge step request shape audit
- P151: Direct workspace write bypass scan

## Results
- R131

## Latest Check
C145

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/README.md
- Ticket T133: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/tickets/T133.md
- Result R131: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/results/R131.md
- Check C145: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/checks/C145.md

## Follow-ups
- none

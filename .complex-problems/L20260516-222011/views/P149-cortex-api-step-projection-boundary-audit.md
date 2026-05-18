# P149: Cortex API step projection boundary audit

Status: done
Parent: P148
Root: P000
Source Ticket: T133 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149/README.md
Ticket(s): T134

## Problem
The Cortex API endpoint that records tool steps must normalize and write structured observations through `write_step_projection`, and tests must prove request data becomes a stored step plus index metadata without inline raw results.

This belongs under `P148` because it is the primary active Cortex write path for tool-step projections.

## Success Criteria
- API request model and handler for step writes are mapped with source pointers.
- The handler calls `normalize_step` and `write_step_projection` or an equivalent strict boundary.
- Tests prove unsafe inline `result` is rejected through the API path.
- Tests prove a valid API request writes a step file and index row with refs/metadata.

## Subproblems
- none

## Results
- R128

## Latest Check
C142

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149/README.md
- Ticket T134: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149/tickets/T134.md
- Result R128: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149/results/R128.md
- Check C142: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P149/checks/C142.md

## Follow-ups
- none

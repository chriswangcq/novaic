# P210: Audit nested result wrapper projection branch

Status: done
Parent: P209
Root: P000
Source Ticket: T198 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210/README.md
Ticket(s): T199

## Problem
`parse_tool_result` still unwraps a nested `result` dict before projection. This may be needed for older persisted tool payloads or may be stale compatibility. Decide branch fate with evidence and tests.

## Success Criteria
- Current/persisted reason for nested `result` unwrapping is proven or the branch is removed.
- Tests reflect the decision.
- History/current-tool projections remain text/manifest-only.

## Subproblems
- none

## Results
- R193

## Latest Check
C207

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210/README.md
- Ticket T199: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210/tickets/T199.md
- Result R193: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210/results/R193.md
- Check C207: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P210/checks/C207.md

## Follow-ups
- none

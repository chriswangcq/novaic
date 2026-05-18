# P630: Cortex Workspace Materialize API Removal

Status: done
Parent: P554
Root: P000
Source Ticket: T626 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P630
Body: problems/P000/children/P005/children/P554/children/P630/README.md
Ticket(s): T627

## Problem
`Workspace.materialize()` is stale direct materialization API residue. Even without production callers, it exposes a tempting path around the intended LogicalFS/sandboxd file-view boundary.

## Success Criteria
- Finds all live references to `Workspace.materialize` and `materialize(` in Cortex workspace/logicalfs code and tests.
- Removes `Workspace.materialize()` or reduces it to a non-public non-bypass path only if a current caller proves necessity.
- Rewrites/deletes tests that exist only to preserve the stale materialize contract.
- Runs focused workspace/logicalfs tests affected by the removal.

## Subproblems
- P633: Workspace Materialize Reference Inventory
- P634: Workspace Materialize Removal and Test Rewrite

## Results
- R626

## Latest Check
C667

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P630/README.md
- Ticket T627: problems/P000/children/P005/children/P554/children/P630/tickets/T627.md
- Result R626: problems/P000/children/P005/children/P554/children/P630/results/R626.md
- Check C667: problems/P000/children/P005/children/P554/children/P630/checks/C667.md

## Follow-ups
- none

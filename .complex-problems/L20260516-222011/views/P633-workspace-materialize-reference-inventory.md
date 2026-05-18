# P633: Workspace Materialize Reference Inventory

Status: done
Parent: P630
Root: P000
Source Ticket: T627 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P630/children/P633
Body: problems/P000/children/P005/children/P554/children/P630/children/P633/README.md
Ticket(s): T628

## Problem
Before removing `Workspace.materialize()`, the repo needs a fresh reference inventory so deletion does not accidentally remove a current path or leave stale tests unclassified.

## Success Criteria
- Records exact scans for `Workspace.materialize`, `def materialize`, `.materialize(`, and broad `materialize(` hits in `novaic-cortex`.
- Classifies each hit as production API, test fixture, LogicalFS-intended materialization, or unrelated.
- Identifies the precise files that must be edited or deleted in the implementation child.

## Subproblems
- none

## Results
- R624

## Latest Check
C665

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P630/children/P633/README.md
- Ticket T628: problems/P000/children/P005/children/P554/children/P630/children/P633/tickets/T628.md
- Result R624: problems/P000/children/P005/children/P554/children/P630/children/P633/results/R624.md
- Check C665: problems/P000/children/P005/children/P554/children/P630/children/P633/checks/C665.md

## Follow-ups
- none

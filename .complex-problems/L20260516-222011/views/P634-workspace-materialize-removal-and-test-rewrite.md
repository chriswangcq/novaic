# P634: Workspace Materialize Removal and Test Rewrite

Status: done
Parent: P630
Root: P000
Source Ticket: T627 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P630/children/P634
Body: problems/P000/children/P005/children/P554/children/P630/children/P634/README.md
Ticket(s): T629

## Problem
After the reference inventory, remove the stale `Workspace.materialize()` API and rewrite/delete tests that only protect the legacy direct materialization contract.

## Success Criteria
- Removes the stale production API and any test-only dependency on it.
- Preserves legitimate LogicalFS materialization behavior if separate from `Workspace.materialize()`.
- Runs focused tests for edited Cortex workspace/logicalfs code.
- Records post-change scans proving the stale API is gone.

## Subproblems
- none

## Results
- R625

## Latest Check
C666

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P630/children/P634/README.md
- Ticket T629: problems/P000/children/P005/children/P554/children/P630/children/P634/tickets/T629.md
- Result R625: problems/P000/children/P005/children/P554/children/P630/children/P634/results/R625.md
- Check C666: problems/P000/children/P005/children/P554/children/P630/children/P634/checks/C666.md

## Follow-ups
- none

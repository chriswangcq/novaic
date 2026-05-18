# P562: Cortex Materialization And Local Fallback Residue Inventory

Status: done
Parent: P553
Root: P000
Source Ticket: T557 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P562
Body: problems/P000/children/P005/children/P553/children/P562/README.md
Ticket(s): T558

## Problem
Search Cortex code for stale direct materialization APIs, local shell execution fallbacks, temporary sandbox path leakage, old `/tmp/novaic-cortex-sandbox-*` assumptions, and compatibility paths that could bypass the intended `Workspace -> MountNamespaceLogicalFS -> sandboxd` boundary. This belongs under P553 because Cortex is the semantic owner of RO/RW and any fallback here can undermine the whole layering model.

## Success Criteria
- Records exact static scan commands and outputs.
- Classifies Cortex hits as intended, risky, removable, or follow-up.
- Specifically classifies `Workspace.materialize()` and any shell/local execution fallback terms.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P566: Cortex Materialize API Residue Classification
- P567: Cortex Shell Fallback And Executor Bypass Classification
- P568: Cortex Stable Path Compatibility Residue Classification
- P570: P562 Child Scan Command Manifests

## Results
- R559

## Latest Check
C596

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P562/README.md
- Ticket T558: problems/P000/children/P005/children/P553/children/P562/tickets/T558.md
- Result R559: problems/P000/children/P005/children/P553/children/P562/results/R559.md
- Check C594: problems/P000/children/P005/children/P553/children/P562/checks/C594.md
- Check C596: problems/P000/children/P005/children/P553/children/P562/checks/C596.md

## Follow-ups
- P570: P562 Child Scan Command Manifests

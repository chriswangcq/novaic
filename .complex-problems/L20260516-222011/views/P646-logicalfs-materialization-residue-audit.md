# P646: LogicalFS Materialization Residue Audit

Status: done
Parent: P632
Root: P000
Source Ticket: T642 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632/children/P646
Body: problems/P000/children/P005/children/P554/children/P632/children/P646/README.md
Ticket(s): T643

## Problem
The codebase must distinguish intended LogicalFS provider materialization from legacy Cortex Workspace/direct local materialization. Any active Cortex-local materialization path would violate the service-boundary model.

## Success Criteria
- Scans materialization terms across Cortex, LogicalFS, sandbox service/core, and runtime where relevant.
- Classifies remaining `materialize` hits as intended lower-layer provider behavior, test naming, docs, or active legacy Cortex fallback.
- Removes or creates a follow-up for any active Cortex/direct workspace materialization residue.

## Subproblems
- none

## Results
- R639

## Latest Check
C680

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P646/README.md
- Ticket T643: problems/P000/children/P005/children/P554/children/P632/children/P646/tickets/T643.md
- Result R639: problems/P000/children/P005/children/P554/children/P632/children/P646/results/R639.md
- Check C680: problems/P000/children/P005/children/P554/children/P632/children/P646/checks/C680.md

## Follow-ups
- none

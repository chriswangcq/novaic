# P003: Wire shell execution path through LogicalFS view then sandboxd

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Shell execution must become a clear sequence: Cortex state adapter creates snapshot, LogicalFS creates a view, sandboxd executes against that view, LogicalFS observes patch, Cortex applies patch.

## Success Criteria
- `Sandbox.exec` or equivalent orchestrator follows the explicit sequence without hidden Cortex reads inside LogicalFS.
- Sandboxd still receives a SDK `SandboxExecSpec` and core substrate stays behind sandboxd.
- Tests prove the request sent to sandboxd contains a LogicalFS view handle/mount input from the LogicalFS package.
- Local fallback remains absent.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none

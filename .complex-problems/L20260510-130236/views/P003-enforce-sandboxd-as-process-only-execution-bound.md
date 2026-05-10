# P003: Enforce sandboxd as process-only execution boundary

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Sandboxd should execute processes over a filesystem view. It must not own Cortex
workspace semantics, subagent layout semantics, Blob persistence semantics, or
display/download semantics.

## Success Criteria
- Sandbox service and SDK contracts are process/view oriented and do not expose
- Cortex Workspace or Blob persistence decisions.
- Deployment/start scripts run the sandbox service and do not reference removed
- sandbox-core packages or old local fallback execution.
- Tests prove sandboxd can execute commands through the intended contract.
- Residue scans show no sandbox-local ownership of `/ro` / `/rw` semantics.

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

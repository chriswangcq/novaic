# P003: Cortex uses sandboxd on the active server path

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Writing sandboxd is not enough; the running Cortex API path must use the sandboxd client for shell execution. Direct in-process execution may remain as an explicit unit-test adapter, but production server startup must wire sandboxd.

## Success Criteria
- Cortex `Sandbox` accepts an explicit process-runner dependency.
- Runtime/API construction uses an injected sandboxd client on the server path.
- `main_cortex` or equivalent startup requires/configures the sandboxd URL.
- Tests prove the API/runtime active path can use an injected runner and that shell commands are no longer pre-wrapped in Cortex when a mount plan is available.

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

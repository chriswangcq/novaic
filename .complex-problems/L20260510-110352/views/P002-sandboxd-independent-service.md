# P002: Sandboxd independent service

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Sandbox process execution currently lives in the Cortex process. It should become an independent base service that owns process spawning and mount namespace command wrapping while remaining business-agnostic.

## Success Criteria
- A new `novaic-sandbox-service` package exposes health and execute endpoints.
- The execute endpoint accepts the common sandboxd contract and runs through common sandbox process primitives.
- The service has no Cortex workspace/blob/agent imports.
- Service tests verify successful execution, mount-plan execution path shape, timeout behavior, and error handling.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none

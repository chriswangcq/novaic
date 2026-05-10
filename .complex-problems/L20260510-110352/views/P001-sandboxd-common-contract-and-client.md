# P001: Sandboxd common contract and client

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
The sandbox execution boundary needs a stable, business-agnostic contract so Cortex can call an independent sandboxd server without importing server internals or passing ad hoc dictionaries. The contract must preserve byte output losslessly and must make mount execution explicit.

## Success Criteria
- `novaic-common` exposes reusable sandboxd request/response types and encode/decode helpers.
- `ProcessSpec` can carry an explicit mount plan without Cortex pre-wrapping shell commands.
- A reusable sandboxd client implements the same process-runner port used by Cortex.
- Unit tests cover byte-safe stdout/stderr transport, mount-plan serialization, timeout/result mapping, and no hidden Cortex/business dependencies.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none

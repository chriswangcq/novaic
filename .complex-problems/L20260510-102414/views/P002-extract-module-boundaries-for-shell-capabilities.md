# P002: Extract module boundaries for shell capabilities, LogicalFS, and process execution

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
`novaic_cortex/sandbox.py` currently owns unrelated concerns. This makes the layering hard to reason about and increases the risk of future changes landing in the wrong layer.

## Success Criteria
- Capability CLI generation is moved to a shell-facing module.
- LogicalFS materialization, mount namespace wrapping, and stable path sanitization are moved to a LogicalFS module.
- Process execution dataclasses/runner are moved to an execution module.
- `sandbox.py` remains the thin public facade/orchestrator.
- Public behavior stays unchanged.

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

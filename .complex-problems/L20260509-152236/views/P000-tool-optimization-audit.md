# P000: Tool optimization audit

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Audit whether tools beyond screenshot/display need optimization under the new file/display/resource-oriented context model. The goal is to identify tool families or infrastructure paths that still risk prompt bloat, hidden context coupling, duplicated display semantics, stale compatibility, or poor explicit resource boundaries.

## Success Criteria
- Use the solve-complex-problems ledger and record the audit as files.
- Inspect current Runtime/Cortex/Business code paths for tool execution, tool result persistence, display projection, payload inspection, user attachment handling, and device tools.
- Classify tool families by optimization priority.
- Identify which tools are already aligned with the desired file/display model and which still need work.
- Produce concrete follow-up implementation ticket candidates without changing production code in this turn.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none

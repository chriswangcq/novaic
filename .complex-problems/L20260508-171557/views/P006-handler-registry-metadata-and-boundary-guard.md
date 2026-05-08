# P006: Handler Registry Metadata And Boundary Guard

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P006
Body: problems/P000/children/P006/README.md
Ticket(s): T006

## Problem
Task handlers are Python functions registered by topic, but the registry does not expose enough declarative metadata to separate real business computation from lifecycle/runtime ownership.

## Success Criteria
- Handler registration exposes metadata such as topic, pool, module, and handler name.
- Tests prove handler modules do not import worker lifecycle, queue DB, or concrete process/runtime ownership.
- Existing handler lookup behavior remains compatible.
- Any misleading hidden lifecycle wiring in handler modules is removed or guarded.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P006/README.md
- Ticket T006: problems/P000/children/P006/tickets/T006.md
- Result R005: problems/P000/children/P006/results/R005.md
- Check C005: problems/P000/children/P006/checks/C005.md

## Follow-ups
- none

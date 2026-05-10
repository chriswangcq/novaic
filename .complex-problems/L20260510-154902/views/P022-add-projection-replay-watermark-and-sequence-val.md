# P022: Add projection replay watermark and sequence validation

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P022
Body: problems/P000/children/P003/children/P022/README.md
Ticket(s): T019

## Problem
Phase 2's projector has basic replay semantics but does not fully satisfy the parent criterion that projection output is generation-checked and rebuildable from the event stream. It needs explicit stream/sequence validation and a snapshot watermark before Phase 2 can be considered complete.

## Success Criteria
- `ContextProjectionSnapshot` includes a deterministic stream watermark, at minimum stream id, root scope id, first seq, and applied seq.
- `project_context_events` rejects mixed stream ids.
- `project_context_events` rejects non-contiguous or out-of-order seq values.
- Empty event projection remains deterministic and documented.
- Tests cover valid watermark, mixed stream rejection, duplicate seq rejection, seq gap rejection, and out-of-order rejection.
- Focused ContextEvent tests pass.

## Subproblems
- none

## Results
- R018

## Latest Check
C019

## Bodies
- Problem: problems/P000/children/P003/children/P022/README.md
- Ticket T019: problems/P000/children/P003/children/P022/tickets/T019.md
- Result R018: problems/P000/children/P003/children/P022/results/R018.md
- Check C019: problems/P000/children/P003/children/P022/checks/C019.md

## Follow-ups
- none

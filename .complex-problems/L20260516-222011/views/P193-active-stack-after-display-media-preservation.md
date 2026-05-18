# P193: Active-stack-after-display media preservation

Status: done
Parent: P189
Root: P000
Source Ticket: T178 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193
Body: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193/README.md
Ticket(s): T180

## Problem
Audit runtime context assembly after step-ref expansion so a `[Active skill stack]` system message following a display tool result does not strip, downgrade, or hide the current display media before the next LLM request.

## Success Criteria
- Map the context/multimodal helper that extracts display perception media into provider-visible content.
- Prove display media survives when a system active-stack message follows the display tool result.
- Prove the original display tool message remains placeholder-only after media extraction.
- Add or verify focused regression coverage for this exact ordering.

## Subproblems
- none

## Results
- R175

## Latest Check
C189

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193/README.md
- Ticket T180: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193/tickets/T180.md
- Result R175: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193/results/R175.md
- Check C189: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P193/checks/C189.md

## Follow-ups
- none

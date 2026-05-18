# P189: Runtime current display selection and active-stack ordering

Status: done
Parent: P185
Root: P000
Source Ticket: T176 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P189
Body: problems/P000/children/P003/children/P127/children/P185/children/P189/README.md
Ticket(s): T178

## Problem
Audit runtime context assembly to ensure current display media is selected by current-round/tool metadata rather than fragile adjacency. The active-stack system message can appear after tool messages, but must not prevent current display media from being attached to the next LLM request.

## Success Criteria
- Map runtime/common code that chooses current display media for LLM context.
- Prove display selection survives a following `[Active skill stack]` system message.
- Prove the tool result message remains small and placeholder-only after display.
- Fix or create follow-up work for any positional or ordering-sensitive branch.

## Subproblems
- P192: Runtime step-ref display projection selection
- P193: Active-stack-after-display media preservation

## Results
- R176

## Latest Check
C190

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P189/README.md
- Ticket T178: problems/P000/children/P003/children/P127/children/P185/children/P189/tickets/T178.md
- Result R176: problems/P000/children/P003/children/P127/children/P185/children/P189/results/R176.md
- Check C190: problems/P000/children/P003/children/P127/children/P185/children/P189/checks/C190.md

## Follow-ups
- none

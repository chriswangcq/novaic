# P192: Runtime step-ref display projection selection

Status: done
Parent: P189
Root: P000
Source Ticket: T178 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192
Body: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192/README.md
Ticket(s): T179

## Problem
Audit runtime step-ref expansion so current `display` tool messages are resolved with `display_perception`, while non-display current tools use `current_tool_result` and historical tools use `history`.

## Success Criteria
- Map `_projection_for_tool_message`, tool-name lookup, latest-tool-call fallback, and Cortex formatted read calls.
- Prove current `display` gets `display_perception`.
- Prove historical `display` does not get `display_perception`.
- Prove current non-display tool messages do not get display media projection.

## Subproblems
- none

## Results
- R174

## Latest Check
C188

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192/README.md
- Ticket T179: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192/tickets/T179.md
- Result R174: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192/results/R174.md
- Check C188: problems/P000/children/P003/children/P127/children/P185/children/P189/children/P192/checks/C188.md

## Follow-ups
- none

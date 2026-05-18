# P166: Cortex prepare handler response shape map

Status: done
Parent: P160
Root: P000
Source Ticket: T150 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166
Body: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166/README.md
Ticket(s): T151

## Problem
`handle_cortex_prepare_llm_context` shapes the prepared messages/tools returned to the saga. Its inputs, output fields, and any local fallback reads must be mapped so the saga receives only the intended prepared snapshot.

## Success Criteria
- `cortex_handlers.py` prepare handler is mapped with line pointers for payload parsing, bridge prepare call, messages/tools/tool_names output, no-tool warning, and active stack injection.
- Any `read_context` or local continuity use inside the handler is classified as active-safe, dead, or stale.
- Existing handler tests are identified and run, or a focused guard is added if response shape is unguarded.

## Subproblems
- none

## Results
- R146

## Latest Check
C160

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166/README.md
- Ticket T151: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166/tickets/T151.md
- Result R146: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166/results/R146.md
- Check C160: problems/P000/children/P003/children/P126/children/P135/children/P160/children/P166/checks/C160.md

## Follow-ups
- none

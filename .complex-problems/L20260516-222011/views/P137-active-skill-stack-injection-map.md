# P137: Active skill stack injection map

Status: done
Parent: P126
Root: P000
Source Ticket: T122 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P137
Body: problems/P000/children/P003/children/P126/children/P137/README.md
Ticket(s): T169

## Problem
Active skill stack instructions are injected into LLM context as system messages. This late injection can affect message ordering and current-round media behavior, so its source and timing must be mapped separately.

## Success Criteria
- The active stack injection source is identified and mapped from projected stack state to final LLM messages.
- Ordering relative to tool results, display results, and provider media projection is documented.
- Tests or fixtures prove active stack injection does not cause current-round display media to be treated as historical text-only output.
- Any duplicate or stale stack-injection path is removed or split into a cleanup follow-up.

## Subproblems
- P180: Active stack source and projection map
- P181: Active stack final context injection ordering map
- P182: Active stack and current display media regression coverage
- P183: Active stack stale injection cleanup audit

## Results
- R170

## Latest Check
C184

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P137/README.md
- Ticket T169: problems/P000/children/P003/children/P126/children/P137/tickets/T169.md
- Result R170: problems/P000/children/P003/children/P126/children/P137/results/R170.md
- Check C184: problems/P000/children/P003/children/P126/children/P137/checks/C184.md

## Follow-ups
- none

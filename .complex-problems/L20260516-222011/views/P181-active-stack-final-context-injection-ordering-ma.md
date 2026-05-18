# P181: Active stack final context injection ordering map

Status: done
Parent: P137
Root: P000
Source Ticket: T169 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P137/children/P181
Body: problems/P000/children/P003/children/P126/children/P137/children/P181/README.md
Ticket(s): T171

## Problem
The `[Active skill stack ...]` system message appears in final LLM context. Its injection point and ordering relative to assistant tool calls, tool results, and context-event messages must be mapped so late system messages do not alter current-round tool-result semantics.

## Success Criteria
- Identify the production code that converts projected active stack state into final LLM messages.
- Document exact ordering relative to tool result expansion and provider-specific formatting.
- Add or tighten tests if ordering is only implied by snapshots or not covered.
- Fix or split any duplicate stack injection path.

## Subproblems
- none

## Results
- R167

## Latest Check
C181

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P137/children/P181/README.md
- Ticket T171: problems/P000/children/P003/children/P126/children/P137/children/P181/tickets/T171.md
- Result R167: problems/P000/children/P003/children/P126/children/P137/children/P181/results/R167.md
- Check C181: problems/P000/children/P003/children/P126/children/P137/children/P181/checks/C181.md

## Follow-ups
- none

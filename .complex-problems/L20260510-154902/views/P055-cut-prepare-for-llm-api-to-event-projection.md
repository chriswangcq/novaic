# P055: Cut prepare_for_llm API to event projection

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P055
Body: problems/P000/children/P005/children/P055/README.md
Ticket(s): T054

## Problem
`/v1/context/prepare_for_llm` still instantiates DFS `ContextEngine` and reads legacy projection files as source. It must use the event projection read adapter as the primary and only source.

## Success Criteria
- `context_prepare_for_llm` no longer imports or instantiates `ContextEngine`.
- Prepared context messages come from ContextEvent projection.
- Focused API tests cover active wake, notification hints, tool results, and closed skills from events.
- No silent DFS fallback exists.

## Subproblems
- none

## Results
- R052

## Latest Check
C055

## Bodies
- Problem: problems/P000/children/P005/children/P055/README.md
- Ticket T054: problems/P000/children/P005/children/P055/tickets/T054.md
- Result R052: problems/P000/children/P005/children/P055/results/R052.md
- Check C055: problems/P000/children/P005/children/P055/checks/C055.md

## Follow-ups
- none

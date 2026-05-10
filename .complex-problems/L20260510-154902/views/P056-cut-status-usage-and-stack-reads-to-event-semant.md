# P056: Cut status usage and stack reads to event semantics

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P056
Body: problems/P000/children/P005/children/P056/README.md
Ticket(s): T055

## Problem
`context_status(include_usage=True)` still renders through DFS `ContextEngine`, and default stack reads still rely on filesystem active stack traversal. Phase 4 needs status usage to come from projection and stack semantics to move toward event replay without breaking LIFO validation.

## Success Criteria
- `context_status(include_usage=True)` uses the event projection read adapter for message/token usage.
- Stack frames returned by status are event projection frames or explicitly justified operational control frames.
- Tests cover include_usage and stack output from event-authored state.
- Any remaining DFS stack traversal is classified as operational validation/debug, not LLM read source.

## Subproblems
- none

## Results
- R053

## Latest Check
C056

## Bodies
- Problem: problems/P000/children/P005/children/P056/README.md
- Ticket T055: problems/P000/children/P005/children/P056/tickets/T055.md
- Result R053: problems/P000/children/P005/children/P056/results/R053.md
- Check C056: problems/P000/children/P005/children/P056/checks/C056.md

## Follow-ups
- none

# P054: Build event projection read adapter

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P054
Body: problems/P000/children/P005/children/P054/README.md
Ticket(s): T053

## Problem
API read paths need a small adapter that reads ordered ContextEvents, replays `project_context_events`, applies budget compaction, and returns messages/stack/token estimates without touching DFS context files.

## Success Criteria
- A reusable read adapter exists for prepared context/status usage.
- Adapter reads from `ContextEventStore` and `project_context_events`.
- Adapter has focused tests for notification hints, active messages, assistant tool calls, tool results, and closed skill summaries.
- Adapter does not fallback to `ContextEngine` or DFS files.

## Subproblems
- none

## Results
- R051

## Latest Check
C054

## Bodies
- Problem: problems/P000/children/P005/children/P054/README.md
- Ticket T053: problems/P000/children/P005/children/P054/tickets/T053.md
- Result R051: problems/P000/children/P005/children/P054/results/R051.md
- Check C054: problems/P000/children/P005/children/P054/checks/C054.md

## Follow-ups
- none

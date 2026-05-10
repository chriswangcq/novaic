# P013: Phase 1.2.2: ContextEvent append and root initialization

Status: done
Parent: P008
Root: P000
Package: problems/P000/children/P002/children/P008/children/P013
Body: problems/P000/children/P002/children/P008/children/P013/README.md
Ticket(s): T007

## Problem
Implement the write side of the ContextEvent store: append one event with generated fields from explicit providers, monotonic sequence assignment, and fresh root stream initialization. This belongs under P008 because later write-path cutover needs one durable append primitive before endpoint migration starts.

## Success Criteria
- Append assigns `seq`, `event_id`, and `occurred_at` from current stream length and injected providers.
- Append validates stream/root identity and event envelope before persisting.
- Multiple appends produce monotonic per-stream ordering.
- Fresh root initialization writes `RootInitialized` without reading or migrating old DFS history.
- Tests cover first append, multiple appends, injected provider determinism, stream/root mismatch rejection, and root initialization.

## Subproblems
- none

## Results
- R004

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P002/children/P008/children/P013/README.md
- Ticket T007: problems/P000/children/P002/children/P008/children/P013/tickets/T007.md
- Result R004: problems/P000/children/P002/children/P008/children/P013/results/R004.md
- Check C005: problems/P000/children/P002/children/P008/children/P013/checks/C005.md

## Follow-ups
- none

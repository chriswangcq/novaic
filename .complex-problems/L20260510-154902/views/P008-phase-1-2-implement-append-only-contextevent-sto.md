# P008: Phase 1.2: Implement append-only ContextEvent store

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P008
Body: problems/P000/children/P002/children/P008/README.md
Ticket(s): T005

## Problem
Implement append/read storage for ContextEvents over the existing Cortex workspace substrate. This belongs under Phase 1 because later cutover phases need one authoritative append path before write endpoints can emit events.

## Success Criteria
- The store can initialize and read a fresh root stream without migrating old DFS history.
- Append produces a monotonic per-stream sequence and stable event id/occurred_at using injected id and clock providers.
- Read returns events in stream order and validates persisted rows.
- Append rejects stream/root mismatches and never overwrites or rewrites existing rows.
- Unit tests cover empty read, first append, multiple appends, stream isolation, explicit clock/id providers, and malformed persisted rows.

## Subproblems
- P012: Phase 1.2.1: ContextEvent store path and read replay
- P013: Phase 1.2.2: ContextEvent append and root initialization

## Results
- R005

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P002/children/P008/README.md
- Ticket T005: problems/P000/children/P002/children/P008/tickets/T005.md
- Result R005: problems/P000/children/P002/children/P008/results/R005.md
- Check C006: problems/P000/children/P002/children/P008/checks/C006.md

## Follow-ups
- none

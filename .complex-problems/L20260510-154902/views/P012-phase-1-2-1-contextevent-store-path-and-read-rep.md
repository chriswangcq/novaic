# P012: Phase 1.2.1: ContextEvent store path and read replay

Status: done
Parent: P008
Root: P000
Package: problems/P000/children/P002/children/P008/children/P012
Body: problems/P000/children/P002/children/P008/children/P012/README.md
Ticket(s): T006

## Problem
Implement the read side of the ContextEvent store: deterministic stream path ownership, empty read behavior, JSONL parsing, persisted row validation, and ordered replay of `ContextEvent` objects. This belongs under P008 because append/read storage must reject corrupt persisted state before later projections trust it.

## Success Criteria
- A `ContextEventStore` or equivalent module defines the event-log path for a root stream.
- Reading a missing event log returns an empty list.
- Reading a valid JSONL log returns ordered validated `ContextEvent` objects.
- Reading malformed JSON or invalid event envelopes raises a clear store/schema error.
- Tests cover empty read, valid ordered read, malformed JSON, invalid event row, and path construction.

## Subproblems
- none

## Results
- R003

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P002/children/P008/children/P012/README.md
- Ticket T006: problems/P000/children/P002/children/P008/children/P012/tickets/T006.md
- Result R003: problems/P000/children/P002/children/P008/children/P012/results/R003.md
- Check C004: problems/P000/children/P002/children/P008/children/P012/checks/C004.md

## Follow-ups
- none

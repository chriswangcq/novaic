# P022: Phase 3B1 Active Stack Projection Helper

Status: done
Parent: P018
Root: P000
Package: problems/P000/children/P004/children/P018/children/P022
Body: problems/P000/children/P004/children/P018/children/P022/README.md
Ticket(s): T017

## Problem
The operational store has `set_active_stack`, but runtime code lacks a small explicit helper for frame schema, generation, top-first ordering, and stack event payloads.

## Success Criteria
- Add a helper module or functions with explicit inputs for root scope id/path, frames, generation, and reason.
- Frames are normalized top-first with stable keys needed by API responses and later active-path routing.
- Helper writes via `OperationalSqliteStore.set_active_stack` and, where needed, appends durable scope/control events with idempotency keys.
- Unit tests cover empty, nested, and malformed frame inputs.

## Subproblems
- none

## Results
- R014

## Latest Check
C015

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P022/README.md
- Ticket T017: problems/P000/children/P004/children/P018/children/P022/tickets/T017.md
- Result R014: problems/P000/children/P004/children/P018/children/P022/results/R014.md
- Check C015: problems/P000/children/P004/children/P018/children/P022/checks/C015.md

## Follow-ups
- none

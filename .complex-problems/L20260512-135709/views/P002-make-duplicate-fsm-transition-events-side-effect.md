# P002: Make duplicate FSM transition events side-effect free

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
The generic FSM transition runner currently treats an idempotent duplicate event as if it were a fresh transition, which can overwrite materialized state and attempt outbox effects. This can create a half-state such as a fresh active scope with no matching wake outbox.

## Success Criteria
- The generic store exposes whether an event insert was fresh or an idempotent replay.
- The generic transition runner skips state and outbox writes on duplicate event replay.
- Existing `append_event()` callers keep their original string return contract.
- A regression test proves duplicate transition replay does not mutate state or create outbox effects.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none

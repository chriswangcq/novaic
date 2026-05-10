# P027: Phase 3B3A Active Stack Finalize Helper

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P018/children/P024/children/P027
Body: problems/P000/children/P004/children/P018/children/P024/children/P027/README.md
Ticket(s): T021

## Problem
P024 needs a durable operational finalize event, but there is not yet a small helper that snapshots the remaining active stack, appends an idempotent SQLite event with an explicit reason/generation, and clears the active-stack projection deterministically. Without this helper, archive call sites will duplicate state-shaping logic.

## Success Criteria
- Add a focused helper for active-stack finalization using explicit operational store, root scope id, frames, generation, reason, and idempotency key.
- Helper writes a durable operational SQLite event containing `remaining_stack`, `top_scope_id`, and `reason`.
- Helper clears the active-stack projection deterministically after recording the event.
- Helper retry with the same idempotency key returns the same event without conflicting duplicate writes.
- Unit tests cover empty and non-empty remaining stack cases.

## Subproblems
- none

## Results
- R017

## Latest Check
C019

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P024/children/P027/README.md
- Ticket T021: problems/P000/children/P004/children/P018/children/P024/children/P027/tickets/T021.md
- Result R017: problems/P000/children/P004/children/P018/children/P024/children/P027/results/R017.md
- Check C019: problems/P000/children/P004/children/P018/children/P024/children/P027/checks/C019.md

## Follow-ups
- none

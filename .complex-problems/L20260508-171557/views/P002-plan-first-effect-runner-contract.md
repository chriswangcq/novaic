# P002: Plan-First Effect Runner Contract

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Action engines still call `execute_effect(...)` directly. Move effect execution ownership into a generic runner/substrate so engines compute explicit actions/plans and effect execution is centralized.

## Success Criteria
- `queue_service/worker/effects.py` exposes a reusable plan runner API.
- Task, saga, scheduler, and health engines no longer import or call `execute_effect(...)` directly.
- `_effect(...)` helper methods are removed from action engines.
- Tests prove action engines stay behind explicit effect adapters and direct effect execution is banned.

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

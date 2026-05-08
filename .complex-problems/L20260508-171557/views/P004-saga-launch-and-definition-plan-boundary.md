# P004: Saga Launch And Definition Plan Boundary

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
Saga launch still publishes tasks and marks state in a direct loop, while saga definitions are DSL-like but callback-heavy. Introduce a deterministic saga launch plan boundary and clarify callback extension points.

## Success Criteria
- Saga launch can produce an explicit plan from saga state, definition, and context.
- Saga launch engine executes through the generic plan/effect substrate.
- Saga definition callback extension points are documented/named and guarded as explicit computation hooks.
- Tests assert saga plan compilation for known saga definitions.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none

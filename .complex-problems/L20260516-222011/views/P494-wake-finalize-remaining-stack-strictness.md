# P494: Wake finalize remaining-stack strictness

Status: done
Parent: P489
Root: P000
Source Ticket: T483 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494
Body: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494/README.md
Ticket(s): T485

## Problem
`wake_finalize.py` currently accepts absent `remaining_stack` and fabricates an empty one. That makes finalize look structurally valid while possibly losing stack state. This belongs under P489 because finalize ownership should require explicit reason, generation, and remaining stack semantics.

## Success Criteria
- `wake_finalize.py` requires `remaining_stack` to be a dict for scope-end and session-ended payloads.
- Legacy fallback synthesis from `stack_known_at_finalize` / `stack_depth_at_finalize` is removed or made unreachable by strict validation.
- Focused tests cover valid pass-through and missing/invalid stack rejection.
- Focused tests pass.

## Subproblems
- none

## Results
- R480

## Latest Check
C509

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494/README.md
- Ticket T485: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494/tickets/T485.md
- Result R480: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494/results/R480.md
- Check C509: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P494/checks/C509.md

## Follow-ups
- none

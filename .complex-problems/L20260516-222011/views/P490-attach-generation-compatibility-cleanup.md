# P490: Attach generation compatibility cleanup

Status: done
Parent: P482
Root: P000
Source Ticket: T481 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P490
Body: problems/P000/children/P004/children/P279/children/P482/children/P490/README.md
Ticket(s): T487

## Problem
Attach handling must reject stale or missing generation inputs through explicit FSM/session state semantics, not legacy fallback behavior. Any no-generation attach compatibility path can make a new message attach to the wrong wake or hide session corruption. This belongs under P482 because attach/generation residue is a direct source of old wake-loop failures.

## Success Criteria
- Attach/generation production paths are inspected against the P482 inventory.
- Missing-generation and stale-generation handling is explicit and deterministic.
- High-confidence legacy no-generation compatibility paths are removed or converted to strict guard behavior.
- Focused attach/generation tests pass.

## Subproblems
- P496: Attach generation contract inventory
- P497: Attach generation contract hardening
- P498: Attach generation final verification

## Results
- R488

## Latest Check
C517

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P490/README.md
- Ticket T487: problems/P000/children/P004/children/P279/children/P482/children/P490/tickets/T487.md
- Result R488: problems/P000/children/P004/children/P279/children/P482/children/P490/results/R488.md
- Check C517: problems/P000/children/P004/children/P279/children/P482/children/P490/checks/C517.md

## Follow-ups
- none

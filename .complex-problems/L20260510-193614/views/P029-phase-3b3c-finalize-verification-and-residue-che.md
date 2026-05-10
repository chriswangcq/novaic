# P029: Phase 3B3C Finalize Verification And Residue Check

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P018/children/P024/children/P029
Body: problems/P000/children/P004/children/P018/children/P024/children/P029/README.md
Ticket(s): T023

## Problem
After helper and wiring work, P024 needs strict verification that finalize semantics are really active and not just implemented beside the live path. The checks must cover empty stacks, non-empty child stacks, retry/idempotency, projection clearing, and old hard-coded empty-stack residue.

## Success Criteria
- API or lifecycle tests cover finalize/archive with an empty stack.
- API or lifecycle tests cover finalize/archive while child stack remains non-empty and assert the operational finalize event contains that remaining stack.
- Retry/idempotency tests prove finalize does not duplicate conflicting events.
- Projection is cleared after finalize in tests.
- Static search confirms no live archive path still hard-codes `remaining_stack=[]` as the authority.
- Targeted and full Cortex tests pass.

## Subproblems
- none

## Results
- R019

## Latest Check
C021

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P024/children/P029/README.md
- Ticket T023: problems/P000/children/P004/children/P018/children/P024/children/P029/tickets/T023.md
- Result R019: problems/P000/children/P004/children/P018/children/P024/children/P029/results/R019.md
- Check C021: problems/P000/children/P004/children/P018/children/P024/children/P029/checks/C021.md

## Follow-ups
- none

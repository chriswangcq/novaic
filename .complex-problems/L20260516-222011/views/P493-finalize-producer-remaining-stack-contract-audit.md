# P493: Finalize producer remaining-stack contract audit

Status: done
Parent: P489
Root: P000
Source Ticket: T483 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493
Body: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493/README.md
Ticket(s): T484

## Problem
Before removing wake finalize fallback stack synthesis, identify every production/test producer of `wake_finalize` context and prove whether it supplies explicit `remaining_stack`. This belongs under P489 because a strict finalizer is only safe if its legitimate producers already meet the contract or can be fixed directly.

## Success Criteria
- All `wake_finalize` context producers are listed with file references.
- Each producer is classified as explicit stack provider, missing provider, or test fixture.
- Missing providers become explicit child/follow-up work instead of preserving fallback.
- Evidence is saved under the ledger tmp directory.

## Subproblems
- none

## Results
- R479

## Latest Check
C508

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493/README.md
- Ticket T484: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493/tickets/T484.md
- Result R479: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493/results/R479.md
- Check C508: problems/P000/children/P004/children/P279/children/P482/children/P489/children/P493/checks/C508.md

## Follow-ups
- none

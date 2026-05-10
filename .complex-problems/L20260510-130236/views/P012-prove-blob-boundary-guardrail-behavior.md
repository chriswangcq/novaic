# P012: Prove Blob Boundary Guardrail Behavior

Status: done
Parent: P007
Root: P000
Package: problems/P000/children/P004/children/P007/children/P012
Body: problems/P000/children/P004/children/P007/children/P012/README.md
Ticket(s): T009

## Problem
A guardrail that merely passes the current tree may still be useless if it cannot catch an obvious bypass. The repo needs evidence that the new guardrail permits allowed paths and rejects direct live `RO` / `RW` bypass shapes.

This child belongs under T006 because it closes the guardrail with positive and negative proof.

## Success Criteria
- Targeted tests pass in the current tree.
- A synthetic negative case or fixture proves obvious direct `/v1/objects`, `BlobCortexStore`, or forbidden `CortexStore` live authority usage is rejected.
- The result records the exact commands and outcomes.

## Subproblems
- none

## Results
- R006

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P004/children/P007/children/P012/README.md
- Ticket T009: problems/P000/children/P004/children/P007/children/P012/tickets/T009.md
- Result R006: problems/P000/children/P004/children/P007/children/P012/results/R006.md
- Check C006: problems/P000/children/P004/children/P007/children/P012/checks/C006.md

## Follow-ups
- none

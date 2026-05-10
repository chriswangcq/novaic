# P034: Phase 3.3.3: Verify context append/batch cutover boundaries

Status: done
Parent: P025
Root: P000
Package: problems/P000/children/P004/children/P025/children/P034
Body: problems/P000/children/P004/children/P025/children/P034/README.md
Ticket(s): T029

## Problem
After append/batch event wiring, audit that there is no hidden direct-only context write path for these endpoints and that remaining legacy `context.jsonl` writes are explicitly transitional.

## Success Criteria
- Focused append/batch event tests pass.
- Full Cortex suite passes.
- Static scans document remaining `context.jsonl` write sites and classify them.
- Any unresolved bypass becomes a follow-up before P025 closes.

## Subproblems
- none

## Results
- R026

## Latest Check
C028

## Bodies
- Problem: problems/P000/children/P004/children/P025/children/P034/README.md
- Ticket T029: problems/P000/children/P004/children/P025/children/P034/tickets/T029.md
- Result R026: problems/P000/children/P004/children/P025/children/P034/results/R026.md
- Check C028: problems/P000/children/P004/children/P025/children/P034/checks/C028.md

## Follow-ups
- none

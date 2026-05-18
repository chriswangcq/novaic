# P165: ReAct saga prepare-context ordering guard

Status: done
Parent: P159
Root: P000
Source Ticket: T147 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165
Body: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165/README.md
Ticket(s): T149

## Problem
Source mapping is not enough; a future edit could reorder or bypass `prepare_context`. A focused test/static guard should fail if `call_llm` stops depending on the prepare-context result.

## Success Criteria
- Existing tests/static guards around `prepare_context` before `call_llm` are identified.
- If no direct guard exists, a small focused guard is added.
- The guard is run with focused runtime tests.
- The result documents exactly which ordering regression the guard catches.

## Subproblems
- none

## Results
- R144

## Latest Check
C158

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165/README.md
- Ticket T149: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165/tickets/T149.md
- Result R144: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165/results/R144.md
- Check C158: problems/P000/children/P003/children/P126/children/P135/children/P159/children/P165/checks/C158.md

## Follow-ups
- none

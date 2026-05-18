# P163: Runtime prepare-context regression coverage audit

Status: done
Parent: P135
Root: P000
Source Ticket: T146 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P163
Body: problems/P000/children/P003/children/P126/children/P135/children/P163/README.md
Ticket(s): T163

## Problem
Even if the handler chain is currently correct, it needs tests that would fail if stale local continuity or `context.read` projections re-enter the final LLM context path.

## Success Criteria
- Existing runtime tests for prepare-context, context ordering, context read-by-id, no-wake replay, and no historical tool-image injection are mapped.
- The selected test set is run after the source mapping children finish.
- Missing guard coverage is added if the source map reveals an unguarded regression path.
- The final coverage result explicitly states which stale-context regression modes are and are not covered.

## Subproblems
- none

## Results
- R159

## Latest Check
C173

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P163/README.md
- Ticket T163: problems/P000/children/P003/children/P126/children/P135/children/P163/tickets/T163.md
- Result R159: problems/P000/children/P003/children/P126/children/P135/children/P163/results/R159.md
- Check C173: problems/P000/children/P003/children/P126/children/P135/children/P163/checks/C173.md

## Follow-ups
- none

# P053: Remove dead runtime scope lifecycle metrics coverage

Status: done
Parent: P050
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053/README.md
Ticket(s): T047

## Problem
`CortexMetrics.scopes_created` and `scopes_archived` were incremented only by removed runtime lifecycle helpers. Tests still assert those counters, which preserves an obsolete runtime ownership model.

## Success Criteria
- Runtime metrics tests no longer assert scope lifecycle counters.
- If no production code owns these counters after runtime helper removal, `CortexMetrics` removes the dead fields and tests are updated accordingly.
- `tests/test_wave4_metrics.py`, remaining metrics assertions in `tests/test_hooks_limits.py`, and metric shape tests pass.

## Subproblems
- none

## Results
- R041

## Latest Check
C044

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053/README.md
- Ticket T047: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053/tickets/T047.md
- Result R041: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053/results/R041.md
- Check C044: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P053/checks/C044.md

## Follow-ups
- none

# P244: Verify mixed runtime and Cortex pytest selection is stable

Status: done
Parent: P241
Root: P000
Source Ticket: T233 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244
Body: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244/README.md
Ticket(s): T236

## Problem
After namespace cleanup, the previously failing mixed focused pytest command must pass in one process. This belongs under the namespace cleanup ticket because the goal is not just local Cortex tests, but cross-package verification stability.

## Success Criteria
- The combined focused command for `novaic-agent-runtime/tests/test_tool_surface_boundary.py` and `novaic-cortex/tests/test_tool_schemas_limits.py` passes in one pytest process.
- A scan confirms Cortex tests no longer contain generic `tests.*` imports.
- Any remaining top-level `tests` package ambiguity is documented as unrelated or removed when it affects the mixed command.

## Subproblems
- none

## Results
- R231

## Latest Check
C245

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244/README.md
- Ticket T236: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244/tickets/T236.md
- Result R231: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244/results/R231.md
- Check C245: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P244/checks/C245.md

## Follow-ups
- none

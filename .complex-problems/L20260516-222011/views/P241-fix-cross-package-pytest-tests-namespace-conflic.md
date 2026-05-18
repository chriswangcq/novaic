# P241: Fix cross-package pytest tests namespace conflict

Status: done
Parent: P239
Root: P000
Source Ticket: none (none)
Source Check: C242
Package: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241
Body: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/README.md
Ticket(s): T233

## Problem
Focused tests from multiple subprojects cannot reliably run in one pytest process because multiple packages expose a top-level `tests` package. In particular, Cortex tests import helpers via `from tests...`, which resolves to the wrong package when `novaic-agent-runtime` appears first on `PYTHONPATH`. This makes schema/policy verification order-dependent and violates the explicit dependency boundary expected for the audit.

## Success Criteria
- Cortex schema tests no longer depend on a generic top-level `tests` package for helper imports.
- A combined focused pytest command covering runtime tool surface policy and Cortex tool schema limits passes in one process.
- The cleanup removes or neutralizes the stale `tests` package ambiguity instead of adding a brittle local fallback.

## Subproblems
- P242: Inventory Cortex test helper imports and package markers
- P243: Migrate Cortex helpers to package-specific test namespace
- P244: Verify mixed runtime and Cortex pytest selection is stable

## Results
- R232

## Latest Check
C246

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/README.md
- Ticket T233: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/tickets/T233.md
- Result R232: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/results/R232.md
- Check C246: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/checks/C246.md

## Follow-ups
- none

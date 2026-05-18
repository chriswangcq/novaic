# P242: Inventory Cortex test helper imports and package markers

Status: done
Parent: P241
Root: P000
Source Ticket: T233 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242
Body: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242/README.md
Ticket(s): T234

## Problem
Before modifying imports, identify every Cortex test dependency on generic `tests.*` imports and the package marker files that create top-level `tests` package ambiguity. This belongs under the namespace cleanup ticket because the implementation should be based on an explicit import inventory rather than a blind replace.

## Success Criteria
- Produce an evidence-backed list of Cortex `tests.*` imports that must change.
- Identify whether `novaic-cortex/tests/__init__.py` has any active purpose beyond making a top-level package.
- Record any non-Cortex `tests.*` dependency that could still affect the combined focused verification command.

## Subproblems
- none

## Results
- R229

## Latest Check
C243

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242/README.md
- Ticket T234: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242/tickets/T234.md
- Result R229: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242/results/R229.md
- Check C243: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P242/checks/C243.md

## Follow-ups
- none

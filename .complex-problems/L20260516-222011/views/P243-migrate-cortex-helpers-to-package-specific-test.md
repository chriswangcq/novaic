# P243: Migrate Cortex helpers to package-specific test namespace

Status: done
Parent: P241
Root: P000
Source Ticket: T233 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243
Body: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243/README.md
Ticket(s): T235

## Problem
Cortex shared test helpers need a package-specific namespace so Cortex tests do not import through generic `tests.*`. This belongs under the namespace cleanup ticket because it is the actual code change that removes order-dependent import behavior.

## Success Criteria
- Cortex helper modules used by tests live under a Cortex-specific helper package or equivalent unambiguous namespace.
- Cortex test files import the unambiguous namespace instead of `tests.*`.
- `novaic-cortex/tests/__init__.py` is removed or proven unnecessary and deleted.
- No compatibility shim preserves the old generic `tests.*` path.

## Subproblems
- none

## Results
- R230

## Latest Check
C244

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243/README.md
- Ticket T235: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243/tickets/T235.md
- Result R230: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243/results/R230.md
- Check C244: problems/P000/children/P003/children/P129/children/P230/children/P239/children/P241/children/P243/checks/C244.md

## Follow-ups
- none

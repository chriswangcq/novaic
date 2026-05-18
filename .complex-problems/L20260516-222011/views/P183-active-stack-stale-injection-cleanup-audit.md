# P183: Active stack stale injection cleanup audit

Status: done
Parent: P137
Root: P000
Source Ticket: T169 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P137/children/P183
Body: problems/P000/children/P003/children/P126/children/P137/children/P183/README.md
Ticket(s): T173

## Problem
Even if current ordering is correct, stale duplicate injection code can reintroduce confusing behavior later. Search for old active-stack collectors, file-walk stack builders, duplicated prompt fragments, and tests that preserve obsolete behavior.

## Success Criteria
- Inventory active-stack-related production and test paths.
- Classify each suspicious path as active, stale, or test-only.
- Remove stale production/test code directly if safe.
- If removal is not safe, create one focused follow-up explaining the dependency that blocks deletion.

## Subproblems
- none

## Results
- R169

## Latest Check
C183

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P137/children/P183/README.md
- Ticket T173: problems/P000/children/P003/children/P126/children/P137/children/P183/tickets/T173.md
- Result R169: problems/P000/children/P003/children/P126/children/P137/children/P183/results/R169.md
- Check C183: problems/P000/children/P003/children/P126/children/P137/children/P183/checks/C183.md

## Follow-ups
- none

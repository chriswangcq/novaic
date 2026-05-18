# P660: Tests Stale Contract Audit

Status: done
Parent: P006
Root: P000
Source Ticket: T657 (split)
Source Check: none
Package: problems/P000/children/P006/children/P660
Body: problems/P000/children/P006/children/P660/README.md
Ticket(s): T659

## Problem
Search tests for old contracts, old paths, compatibility assertions, or test helpers that preserve stale behavior instead of current architecture.

## Success Criteria
- Runs focused scans over tests for old path/tool/compatibility terms.
- Inspects high-risk hits in Cortex/runtime/common/business where contract drift matters.
- Rewrites or deletes tests that only protect stale behavior.
- Runs affected test files after any changes.

## Subproblems
- none

## Results
- R657

## Latest Check
C699

## Bodies
- Problem: problems/P000/children/P006/children/P660/README.md
- Ticket T659: problems/P000/children/P006/children/P660/tickets/T659.md
- Result R657: problems/P000/children/P006/children/P660/results/R657.md
- Check C699: problems/P000/children/P006/children/P660/checks/C699.md

## Follow-ups
- none

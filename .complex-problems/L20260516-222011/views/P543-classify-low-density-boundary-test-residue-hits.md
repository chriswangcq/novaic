# P543: Classify low-density boundary test residue hits

Status: done
Parent: P535
Root: P000
Source Ticket: T535 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543
Body: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543/README.md
Ticket(s): T538

## Problem
Classify the remaining low-density test residue hits not owned by the high-density lifecycle/recovery or cutover/guardrail groups. This group prevents many one-off test hits from being hand-waved as harmless.

Initial file group:
- All files in `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt` that are not listed in the two high-density child groups.

## Success Criteria
- Remaining test hit count and file count are recorded.
- Every remaining test file gets a purpose/category rationale, even if it has only one hit.
- Stale or misleading one-off tests become follow-up.
- This group does not double-count files assigned to the high-density child groups.

## Subproblems
- P545: Classify low-density tests with 2-4 hits
- P546: Classify single-hit boundary tests
- P547: Reconcile low-density test residue classification

## Results
- R535

## Latest Check
C569

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543/README.md
- Ticket T538: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543/tickets/T538.md
- Result R535: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543/results/R535.md
- Check C569: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P543/checks/C569.md

## Follow-ups
- none

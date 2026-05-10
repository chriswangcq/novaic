# P054: Phase 5B3.3 Legacy Test And Comment Wording Cleanup

Status: done
Parent: P051
Root: P000
Package: problems/P000/children/P006/children/P046/children/P051/children/P054
Body: problems/P000/children/P006/children/P046/children/P051/children/P054/README.md
Ticket(s): T052

## Problem
Some live tests and comments use `legacy` or migration wording even when they now describe current explicit contracts or guard behavior. This makes residue harder to audit and can encourage future compatibility paths.

## Success Criteria
- Rename tests whose `legacy` wording refers to current explicit behavior rather than historical guard scenarios.
- Preserve tests that intentionally prove old legacy behavior is removed, but make their purpose explicit.
- Clean stale compatibility/legacy comments in live source where they are not documenting a current migration or removal guard.
- Do not touch historical design/review docs; Phase 5C owns current documentation/comment sweep beyond this source/test cleanup.
- Targeted context-event no-compat and projection tests pass.

## Subproblems
- none

## Results
- R048

## Latest Check
C051

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P051/children/P054/README.md
- Ticket T052: problems/P000/children/P006/children/P046/children/P051/children/P054/tickets/T052.md
- Result R048: problems/P000/children/P006/children/P046/children/P051/children/P054/results/R048.md
- Check C051: problems/P000/children/P006/children/P046/children/P051/children/P054/checks/C051.md

## Follow-ups
- none

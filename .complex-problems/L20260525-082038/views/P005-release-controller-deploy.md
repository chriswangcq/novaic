# P005: Release Controller deploy

Status: done
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P005
Body: problems/P000/children/P003/children/P005/README.md
Ticket(s): T005

## Problem
Deploy the new source through the centralized Release Controller, not by manually invoking backend service deploy scripts.

## Success Criteria
- Release Controller is healthy and its worktree sees the pushed parent commit.
- A staging release is triggered/executed for the new commit.
- The same release/image is promoted to prod through Release Controller.
- The deployed prod containers run the new immutable image/tag.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P003/children/P005/README.md
- Ticket T005: problems/P000/children/P003/children/P005/tickets/T005.md
- Result R003: problems/P000/children/P003/children/P005/results/R003.md
- Check C003: problems/P000/children/P003/children/P005/checks/C003.md

## Follow-ups
- none

# P005: Release Controller deploy

Status: todo
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P005
Body: problems/P000/children/P003/children/P005/README.md
Ticket(s): none

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
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P003/children/P005/README.md

## Follow-ups
- none

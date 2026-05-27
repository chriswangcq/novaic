# P007: Run final pre-push focused verification

Status: done
Parent: P002
Root: P000
Source Ticket: T004 (split)
Source Check: none
Package: problems/P000/children/P002/children/P007
Body: problems/P000/children/P002/children/P007/README.md
Ticket(s): T005

## Problem
Before committing deployable source, touched code should have fresh focused verification evidence so the pushed commit is not stale relative to local tests.

## Success Criteria
- Focused tests pass for `novaic-llm-factory` streaming route/provider behavior.
- Focused tests pass for `novaic-agent-runtime` stream parsing, handler, and projection behavior.
- Focused tests pass for `novaic-app` timeline/contract guard behavior or App is explicitly marked non-server-release-only.
- Git status for touched repos is captured before commit.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/children/P007/README.md
- Ticket T005: problems/P000/children/P002/children/P007/tickets/T005.md
- Result R003: problems/P000/children/P002/children/P007/results/R003.md
- Check C003: problems/P000/children/P002/children/P007/checks/C003.md

## Follow-ups
- none

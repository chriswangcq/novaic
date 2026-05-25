# P003: Verify, clean, and commit structured activity title change

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
The cross-repo change must be proven and committed cleanly. The current working tree already contains a frontend hotfix; the final state must include runtime/frontend/contract tests, a focused diff review, and commits in affected subrepos plus the parent repo gitlink update.

## Success Criteria
- Focused runtime tests pass.
- Focused frontend ActivityTimeline tests pass.
- Relevant lint/type checks are run; unrelated pre-existing failures are documented.
- Git status is reviewed to avoid unrelated changes.
- Affected subrepos are committed with clear messages.
- Parent repo is committed with updated submodule pointers and ledger artifacts.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none

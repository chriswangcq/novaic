# P005: Update residue guards, tests, and ledger evidence

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T005

## Problem
After code deletion, tests and guard scripts must stop encoding SQLite compatibility as a desirable server property. The work also needs durable evidence so future cleanup does not regress.

## Success Criteria
- Tests/guard scripts assert Postgres-only server persistence where relevant.
- A residue inventory categorizes remaining SQLite references into current allowed, historical archive, or follow-up-required.
- The ledger records evidence from diffs, scans, and test runs.
- Touched submodules and root pointers are committed and pushed without reverting unrelated worktree changes.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T005: problems/P000/children/P005/tickets/T005.md
- Result R004: problems/P000/children/P005/results/R004.md
- Check C004: problems/P000/children/P005/checks/C004.md

## Follow-ups
- none

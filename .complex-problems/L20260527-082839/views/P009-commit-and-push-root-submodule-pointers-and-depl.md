# P009: Commit and push root submodule pointers and deployment ledger

Status: doing
Parent: P002
Root: P000
Source Ticket: T004 (split)
Source Check: none
Package: problems/P000/children/P002/children/P009
Body: problems/P000/children/P002/children/P009/README.md
Ticket(s): T007

## Problem
The Release Controller reads the root repo commit, so root must record updated submodule pointers for server-relevant repos and the deployment ledger state.

## Success Criteria
- Root commit includes updated submodule pointers for pushed subrepo commits and `.complex-problems` deployment/reasoning ledgers.
- Unrelated `CLAUDE.md` is not staged.
- Root `origin/main` contains the commit to trigger.
- Final root commit SHA is recorded for Release Controller trigger.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P002/children/P009/README.md
- Ticket T007: problems/P000/children/P002/children/P009/tickets/T007.md

## Follow-ups
- none

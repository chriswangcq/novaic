# P004: Commit and push release source

Status: doing
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P004
Body: problems/P000/children/P003/children/P004/README.md
Ticket(s): T004

## Problem
The Entangled fix and active ledger changes must be committed in the correct repositories and pushed so Release Controller can build from immutable source.

## Success Criteria
- Entangled submodule has a focused commit with the SQL fix and tests.
- Parent repo has a commit updating the Entangled pointer and ledger.
- Both commits are pushed to their remotes.
- Local git status after commit/push contains no unintentional source edits.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P003/children/P004/README.md
- Ticket T004: problems/P000/children/P003/children/P004/tickets/T004.md

## Follow-ups
- none

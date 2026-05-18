# P523: Repair Session Repository Wrapper Boundary Count Failure

Status: done
Parent: P520
Root: P000
Source Ticket: T514 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523
Body: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523/README.md
Ticket(s): T517

## Problem
`test_session_repository_no_longer_owns_outbox_append_publish_helpers` expects two `require_outbox=True` occurrences in `session_repo.py`, but current source has one.

## Success Criteria
- Determine whether the source or test expectation is stale.
- Apply minimal correct update.
- Rerun the failing test successfully.

## Subproblems
- none

## Results
- R512

## Latest Check
C543

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523/README.md
- Ticket T517: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523/tickets/T517.md
- Result R512: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523/results/R512.md
- Check C543: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P523/checks/C543.md

## Follow-ups
- none

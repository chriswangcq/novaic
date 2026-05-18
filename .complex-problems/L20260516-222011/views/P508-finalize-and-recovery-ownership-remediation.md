# P508: Finalize and recovery ownership remediation

Status: done
Parent: P280
Root: P000
Source Ticket: T502 (split)
Source Check: none
Package: problems/P000/children/P004/children/P280/children/P508
Body: problems/P000/children/P004/children/P280/children/P508/README.md
Ticket(s): T504

## Problem
The ownership map may reveal active gaps where finalize, watchdog, or recovery paths can mutate session state or archive scopes outside the intended event/FSM/outbox ownership model.

## Success Criteria
- Any concrete active ownership gap from the map is fixed or split into a smaller follow-up.
- Required compensation/recovery paths are retained and documented rather than deleted.
- Focused tests are added or updated for any changed behavior.
- If no source change is needed, the result explicitly explains why the map found no active gap.

## Subproblems
- none

## Results
- R501

## Latest Check
C530

## Bodies
- Problem: problems/P000/children/P004/children/P280/children/P508/README.md
- Ticket T504: problems/P000/children/P004/children/P280/children/P508/tickets/T504.md
- Result R501: problems/P000/children/P004/children/P280/children/P508/results/R501.md
- Check C530: problems/P000/children/P004/children/P280/children/P508/checks/C530.md

## Follow-ups
- none

# P001: Verify and recover production IM session state

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
The affected production message must be accounted for after the Redis/disk incident and manual replay. We need evidence that the notification was processed, an agent reply was written, the session returned to `no_active`, and Redis/disk are healthy.

## Success Criteria
- The affected notification is `processed`.
- A corresponding agent reply exists in `environment_im_messages`.
- The queue session state for the affected agent/subagent is `no_active`.
- Redis persistence and disk usage are healthy.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none

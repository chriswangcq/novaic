# P003: Deploy and production smoke

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Deploy the repair to production and run a controlled smoke check proving a new user IM reaches queue/session runtime state and no longer fails silently before agent monitor activity.

## Success Criteria
- Code is deployed to `root@api.gradievo.com`.
- Relevant services are restarted and healthy.
- Smoke input is observed in Entangled.
- Matching notification does not end in dispatch failure.
- Queue/session runtime records input/session activity for the smoke input.
- Logs no longer show the same dispatch timeout and saga claim 500 loop for the smoke window.

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

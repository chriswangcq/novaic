# P001: Code repair queue dispatch and saga claim

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Patch the runtime/common code so Business subscriber dispatch does not use the default 5s httpx timeout and Queue Service saga claim/FSM event writes do not fail with `sqlite3.OperationalError: database is locked` under normal concurrent worker polling.

## Success Criteria
- Relevant code paths are identified and patched.
- Patch is scoped to dispatch timeout and queue-service SQLite/FSM claim reliability.
- No old bypass branch is introduced.

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

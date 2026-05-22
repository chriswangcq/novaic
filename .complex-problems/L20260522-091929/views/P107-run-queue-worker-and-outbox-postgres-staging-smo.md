# P107: Run Queue Worker And Outbox Postgres Staging Smokes

Status: done
Parent: P076
Root: P000
Source Ticket: T103 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P107
Body: problems/P000/children/P024/children/P028/children/P076/children/P107/README.md
Ticket(s): T118

## Problem
Queue Service API smokes do not prove workers and outbox workers can run against Postgres mode. Representative worker processes must connect through Queue Service, avoid SQLite queue file usage, and successfully process or drain staging-safe work.

## Success Criteria
- Representative task worker process starts against the staging Queue Service.
- Saga worker or safe saga worker equivalent starts against staging Queue Service.
- Session/saga outbox worker or safe drain equivalent runs against staging Postgres mode.
- Logs/process checks show no new SQLite `queue.db` holder for the staging queue path.
- Worker/outbox outcomes and DB counts are recorded.

## Subproblems
- none

## Results
- R115

## Latest Check
C130

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P107/README.md
- Ticket T118: problems/P000/children/P024/children/P028/children/P076/children/P107/tickets/T118.md
- Result R115: problems/P000/children/P024/children/P028/children/P076/children/P107/results/R115.md
- Check C130: problems/P000/children/P024/children/P028/children/P076/children/P107/checks/C130.md

## Follow-ups
- none

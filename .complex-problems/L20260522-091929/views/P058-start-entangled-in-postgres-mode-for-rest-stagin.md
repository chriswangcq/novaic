# P058: Start Entangled In Postgres Mode For REST Staging

Status: done
Parent: P051
Root: P000
Source Ticket: T052 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058
Body: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058/README.md
Ticket(s): T054

## Problem
After a safe target exists, Entangled must start in Postgres mode and prove readiness without touching the active SQLite file. This belongs under `P051` because REST smokes are only meaningful against a running Postgres-mode service.

## Success Criteria
- A staging/local Entangled process starts with `--db-backend postgres` against the safe target on a non-conflicting loopback port.
- `/v1/health` and `/v1/ready` return success.
- Process arguments show Postgres mode and do not expose secrets.
- File-handle checks show the staging process is not opening active SQLite database files.
- Startup/schema logs are inspected for Postgres DDL or readiness errors.
- The staging process lifecycle is recorded, including cleanup/stop instructions or confirmation.

## Subproblems
- none

## Results
- R050

## Latest Check
C052

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058/README.md
- Ticket T054: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058/tickets/T054.md
- Result R050: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058/results/R050.md
- Check C052: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P058/checks/C052.md

## Follow-ups
- none

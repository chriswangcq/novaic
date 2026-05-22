# P032: Execute Gateway Production Cutover

Status: done
Parent: P030
Root: P000
Source Ticket: T027 (split)
Source Check: none
Package: problems/P000/children/P024/children/P025/children/P030/children/P032
Body: problems/P000/children/P024/children/P025/children/P030/children/P032/README.md
Ticket(s): T029

## Problem
After preflight succeeds, Gateway production must be backed up, migrated to `novaic_gateway`, deployed with the new storage code/dependency, restarted with the Postgres backend, and verified.

## Success Criteria
- `/opt/novaic/data/gateway.db` backup is created before migration.
- Gateway code/dependencies supporting Postgres are deployed.
- `users`, `refresh_tokens`, and `config` are migrated with row-count checks.
- Gateway startup uses `--db-backend postgres --postgres-dsn-file <path>`.
- Gateway health and representative auth/config smoke checks pass after restart.
- No active process writes to `gateway.db` after cutover.
- Central classification note and rollback notes are updated.

## Subproblems
- none

## Results
- R026

## Latest Check
C026

## Bodies
- Problem: problems/P000/children/P024/children/P025/children/P030/children/P032/README.md
- Ticket T029: problems/P000/children/P024/children/P025/children/P030/children/P032/tickets/T029.md
- Result R026: problems/P000/children/P024/children/P025/children/P030/children/P032/results/R026.md
- Check C026: problems/P000/children/P024/children/P025/children/P030/children/P032/checks/C026.md

## Follow-ups
- none

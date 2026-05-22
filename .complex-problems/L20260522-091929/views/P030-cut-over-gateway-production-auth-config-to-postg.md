# P030: Cut Over Gateway Production Auth Config to Postgres

Status: done
Parent: P025
Root: P000
Source Ticket: T025 (split)
Source Check: none
Package: problems/P000/children/P024/children/P025/children/P030
Body: problems/P000/children/P024/children/P025/children/P030/README.md
Ticket(s): T027

## Problem
After Gateway has a Postgres storage path, production Gateway data must be backed up, migrated from `/opt/novaic/data/gateway.db` to `novaic_gateway`, and the runtime must be switched so active auth/config state no longer uses SQLite.

## Success Criteria
- `/opt/novaic/data/gateway.db` is backed up before mutation.
- `users`, `refresh_tokens`, and `config` are migrated to `novaic_gateway` with row-count checks.
- Gateway runtime is switched to Postgres and service health passes.
- Representative auth/config smoke checks pass after cutover.
- No active SQLite writes to `gateway.db` occur after cutover.
- The central SQLite classification note marks `gateway.db` rollback-only/non-current.
- Rollback steps and snapshot location are recorded.

## Subproblems
- P031: Gateway Production Cutover Preflight
- P032: Execute Gateway Production Cutover

## Results
- R027

## Latest Check
C027

## Bodies
- Problem: problems/P000/children/P024/children/P025/children/P030/README.md
- Ticket T027: problems/P000/children/P024/children/P025/children/P030/tickets/T027.md
- Result R027: problems/P000/children/P024/children/P025/children/P030/results/R027.md
- Check C027: problems/P000/children/P024/children/P025/children/P030/checks/C027.md

## Follow-ups
- none

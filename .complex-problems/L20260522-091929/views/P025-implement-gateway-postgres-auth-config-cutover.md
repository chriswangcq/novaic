# P025: Implement Gateway Postgres Auth Config Cutover

Status: done
Parent: P024
Root: P000
Source Ticket: T024 (split)
Source Check: none
Package: problems/P000/children/P024/children/P025
Body: problems/P000/children/P024/children/P025/README.md
Ticket(s): T025

## Problem
Gateway still owns active auth/config state in `/opt/novaic/data/gateway.db`. It should be migrated to the existing `novaic_gateway` Postgres database without carrying retired zero-row Gateway tables or maintaining production SQLite fallback logic.

## Success Criteria
- Gateway has a Postgres-backed production storage path for `users`, `refresh_tokens`, and `config`.
- Retired zero-row Gateway tables are not recreated in Postgres.
- Existing Gateway SQLite state is backed up and migrated with row-count checks.
- Gateway runtime config is switched to Postgres and health/auth smoke checks pass.
- Gateway no longer writes active state to `/opt/novaic/data/gateway.db`.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.

## Subproblems
- P029: Implement Gateway Postgres Storage Path
- P030: Cut Over Gateway Production Auth Config to Postgres

## Results
- R028

## Latest Check
C028

## Bodies
- Problem: problems/P000/children/P024/children/P025/README.md
- Ticket T025: problems/P000/children/P024/children/P025/tickets/T025.md
- Result R028: problems/P000/children/P024/children/P025/results/R028.md
- Check C028: problems/P000/children/P024/children/P025/checks/C028.md

## Follow-ups
- none

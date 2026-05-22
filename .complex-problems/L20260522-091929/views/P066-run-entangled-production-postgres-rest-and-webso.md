# P066: Run Entangled Production Postgres REST And WebSocket Smokes

Status: done
Parent: P042
Root: P000
Source Ticket: T061 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P066
Body: problems/P000/children/P024/children/P027/children/P042/children/P066/README.md
Ticket(s): T068

## Problem
After production Entangled starts in Postgres mode, representative REST and WebSocket behavior must be verified before active SQLite files are moved out of the production path. This belongs under `P042` because runtime health alone is not enough to prove the cutover works.

## Success Criteria
- Representative REST read smoke passes against production Postgres-mode Entangled.
- A bounded REST write/update/delete or explicitly safe equivalent passes without corrupting production data.
- WebSocket schema/list/stream/delta/reconnect smoke passes or records the smallest justified direct protocol equivalent.
- Postgres counts or key semantic values remain sane after smokes.
- Reports/log checks confirm no raw DSN/token/JWT values are recorded.
- Any smoke-created production test rows are cleaned up or explicitly marked harmless.

## Subproblems
- none

## Results
- R065

## Latest Check
C068

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P066/README.md
- Ticket T068: problems/P000/children/P024/children/P027/children/P042/children/P066/tickets/T068.md
- Result R065: problems/P000/children/P024/children/P027/children/P042/children/P066/results/R065.md
- Check C068: problems/P000/children/P024/children/P027/children/P042/children/P066/checks/C068.md

## Follow-ups
- none

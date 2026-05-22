# P072: Restart Business Services After Entangled Postgres Cutover

Status: done
Parent: P042
Root: P000
Source Ticket: none (none)
Source Check: C071
Package: problems/P000/children/P024/children/P027/children/P042/children/P072
Body: problems/P000/children/P024/children/P027/children/P042/children/P072/README.md
Ticket(s): T071

## Problem
The Entangled SQLite-to-Postgres cutover is complete, but Business API and Business subscriber remain stopped from the writer-free cutover window. They must be restarted against the PG-mode Entangled runtime and verified before the production cutover is operationally complete.

## Success Criteria
- Business API is running on its production loopback port and points at `http://127.0.0.1:19900` for Entangled.
- Business subscriber is running with the production service paths/config.
- Business health/readiness or representative endpoint checks pass.
- Business schema push/startup does not reintroduce Entangled schema errors.
- Entangled remains health/ready HTTP 200 with 22 entities after Business restart.
- No process recreates or holds `/opt/novaic/data/entangled.db*`.
- Process/log inspection records no raw DSN/token/JWT values.
- A restart verification report is recorded in ledger artifacts.

## Subproblems
- none

## Results
- R069

## Latest Check
C072

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P072/README.md
- Ticket T071: problems/P000/children/P024/children/P027/children/P042/children/P072/tickets/T071.md
- Result R069: problems/P000/children/P024/children/P027/children/P042/children/P072/results/R069.md
- Check C072: problems/P000/children/P024/children/P027/children/P042/children/P072/checks/C072.md

## Follow-ups
- none

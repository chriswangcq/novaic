# P065: Restart Production Entangled In Postgres Mode

Status: done
Parent: P042
Root: P000
Source Ticket: T061 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P065
Body: problems/P000/children/P024/children/P027/children/P042/children/P065/README.md
Ticket(s): T064

## Problem
After final migration succeeds, production Entangled must be restarted on the existing production port using Postgres and file-based secrets. This belongs under `P042` because the cutover is not complete until the production runtime serves from Postgres instead of SQLite.

## Success Criteria
- Existing SQLite-mode Entangled process is stopped in the controlled cutover window.
- Entangled starts on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Process args do not contain raw DSN or raw service-token values.
- Health/readiness return success after restart.
- No process holds `/opt/novaic/data/entangled.db*` after restart.
- A rollback command/path is recorded if the Postgres-mode runtime fails.

## Subproblems
- P068: Repair Entangled Postgres Placeholder Escaping And Complete Production Readiness

## Results
- R061

## Latest Check
C067

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P065/README.md
- Ticket T064: problems/P000/children/P024/children/P027/children/P042/children/P065/tickets/T064.md
- Result R061: problems/P000/children/P024/children/P027/children/P042/children/P065/results/R061.md
- Check C063: problems/P000/children/P024/children/P027/children/P042/children/P065/checks/C063.md
- Check C067: problems/P000/children/P024/children/P027/children/P042/children/P065/checks/C067.md

## Follow-ups
- P068: Repair Entangled Postgres Placeholder Escaping And Complete Production Readiness

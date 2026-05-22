# P068: Repair Entangled Postgres Placeholder Escaping And Complete Production Readiness

Status: done
Parent: P065
Root: P000
Source Ticket: none (none)
Source Check: C063
Package: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068
Body: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/README.md
Ticket(s): T065

## Problem
The production Entangled process was restarted in Postgres mode, but Business schema registration fails because `PostgresDatabase._convert_placeholders` converts SQLite-style `?` placeholders to `%s` without escaping literal `%` characters for psycopg. The PG runtime is alive on `127.0.0.1:19900`, but readiness is HTTP 503 with zero registered entities.

Repair the placeholder conversion, prove it with local tests, deploy the fix to the API host, restart the PG-mode Entangled runtime using file-backed secrets, push Business and Device schemas without unfreezing writers, and verify readiness succeeds before the cutover can proceed.

## Success Criteria
- Local Entangled Postgres placeholder conversion escapes literal `%` characters while preserving `?` to `%s` conversion.
- A focused regression test covers DDL containing a literal pattern such as `LIKE 'blob://%'`.
- Relevant local Entangled tests pass after the fix.
- The patched Entangled code is deployed to `/opt/novaic/services/Entangled/packages/server-python` on `api.gradievo.com`.
- Production Entangled is restarted on `127.0.0.1:19900` in Postgres mode using `--postgres-dsn-file` and `--service-token-file`.
- Business and Device schemas are registered against Entangled while Business API/subscriber remain frozen.
- `/v1/health` and `/v1/ready` both return HTTP 200 with the expected registered entity count.
- No process holds `/opt/novaic/data/entangled.db*`.
- Process args still contain no raw DSN or raw service-token values.

## Subproblems
- P069: Fix Entangled Postgres Percent Placeholder Escaping Locally
- P070: Deploy Repaired Entangled Runtime And Restore Production Readiness

## Results
- R064

## Latest Check
C066

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/README.md
- Ticket T065: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/tickets/T065.md
- Result R064: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/results/R064.md
- Check C066: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/checks/C066.md

## Follow-ups
- none

# P070: Deploy Repaired Entangled Runtime And Restore Production Readiness

Status: done
Parent: P068
Root: P000
Source Ticket: T065 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070
Body: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070/README.md
Ticket(s): T067

## Problem
After the local placeholder fix is validated, the repaired Entangled adapter must be deployed to `api.gradievo.com`, the current PG-mode runtime on `127.0.0.1:19900` must be restarted with file-backed secrets, and production Business/Device schemas must be registered while Business writers remain frozen.

This child belongs under P068 because it closes the production half of the readiness gap after the local code defect is repaired.

## Success Criteria
- The patched Entangled adapter is deployed under `/opt/novaic/services/Entangled/packages/server-python` on `api.gradievo.com`.
- The PG-mode Entangled process is restarted on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Business schemas are pushed directly to Entangled using the production service token file.
- Device schemas are pushed directly to Entangled without relying on the frozen Business proxy.
- Business API/subscriber remain frozen during the schema push and readiness repair.
- `/v1/health` and `/v1/ready` both return HTTP 200 with the expected registered entity set.
- No process holds `/opt/novaic/data/entangled.db*`.
- Process args contain no raw DSN or raw service-token values.
- A redacted production readiness repair report is recorded in ledger artifacts.

## Subproblems
- none

## Results
- R063

## Latest Check
C065

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070/README.md
- Ticket T067: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070/tickets/T067.md
- Result R063: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070/results/R063.md
- Check C065: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P070/checks/C065.md

## Follow-ups
- none

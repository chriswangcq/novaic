# Deploy Repaired Entangled Runtime And Restore Production Readiness

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

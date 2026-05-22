# Deploy Repaired Entangled Runtime And Restore Production Readiness Check

## Summary

P070 is successful. Result `R063` deployed the local placeholder fix to the API host, restarted production Entangled in Postgres mode, registered Business and Device schemas while Business writers remained frozen, and verified Entangled readiness with the expected 22 entities.

## Evidence

- Remote deployment inspection reported the percent-escape patch present in the deployed `database.py`.
- Production Entangled PID `3566057` is listening on `127.0.0.1:19900`.
- `/v1/health` returned HTTP 200 with 22 entities.
- `/v1/ready` returned HTTP 200 with `status: ready`, 22 entities, and no missing entities.
- Redacted process inspection reported `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`, with no raw DSN/token in args.
- Business schema push registered 20 expected Business entities.
- Device schema push registered `devices` and `vm-users` directly against Entangled.
- `lsof` found zero holders for `/opt/novaic/data/entangled.db*`.
- Business freeze inspection found zero matching Business API/subscriber processes.
- The repair report's production log error tail is empty after the repaired restart and schema push.

## Criteria Map

- Patched adapter deployed to API host: satisfied by remote deployed file inspection.
- Broken PG-mode process replaced: satisfied by new PID `3566057` and listener verification.
- File-backed DSN/token args used: satisfied by process args flags.
- Business schemas register: satisfied by 20 expected Business entity registrations and ready entity list.
- Device schemas register without Business proxy: satisfied by direct registration of `devices` and `vm-users`.
- Business remains frozen: satisfied by zero matching Business API/subscriber processes.
- Health/readiness return HTTP 200: satisfied by final curl checks.
- Registered entity set recorded: satisfied by the local and remote readiness repair report.
- No SQLite holders: satisfied by `lsof` count `0`.
- No raw secrets in process args: satisfied by `raw_dsn_or_token_in_args: false`.
- Redacted production readiness repair report recorded: satisfied by `.complex-problems/L20260522-091929/artifacts/entangled-production-readiness-repair-report.json`.

## Execution Map

- T067 was executed as a bounded one-go production repair.
- R063 recorded the deployed file, restarted runtime, schema pushes, verification, and remaining later-step gaps.
- No runtime child problem was needed because the repaired schema registration succeeded.

## Stress Test

- The main failure mode was the exact production failure shape: schema registration with literal `%` DDL. The Business schema push completed after deploying the fix, which exercises that path against the production Entangled process.
- A second failure mode was accidentally depending on the frozen Business proxy for Device schemas. P070 bypassed the proxy and posted Device specs directly to Entangled.
- Secret exposure risk was checked by process args inspection and by recording only file paths/counts/names in artifacts.

## Residual Risk

- Business API/subscriber are still intentionally frozen and must be restarted/verified in the later production smoke step. This is not a blocker for P070 because P070's scope is restoring Entangled PG readiness without unfreezing writers.
- SQLite residue cleanup remains assigned to the later archive cleanup step.

## Result IDs

- R063

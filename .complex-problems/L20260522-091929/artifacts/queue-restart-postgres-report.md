# Queue Restart In Postgres Mode Report

## Summary

- Status: success
- Queue Service URL: `http://127.0.0.1:19997`
- Queue Service backend: postgres
- Ready status: 200
- Old SQLite holders: none
- Runtime: `/opt/novaic/services/novaic-agent-runtime-pg`

## Process Roles

- Queue Service: 1
- Task workers: 4
- Saga workers: 2
- Session outbox worker: 1
- Saga outbox worker: 1
- Queue health worker: 1
- Queue scheduler: 1
- Business subscriber: 1
- Gateway queue ingress: 1

## Direct Queue DB Processes

- Queue Service environment: Postgres backend and credential file set
- Session outbox worker environment: Postgres backend and credential file set
- Saga outbox worker environment: Postgres backend and credential file set

## Verification

- `/health`: healthy, `database_backend=postgres`
- `/ready`: 200
- `lsof /opt/novaic/data/queue.db`: no holder PIDs
- Role count mismatches: none

## Artifacts

- Remote restart report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-restart-postgres-report.json`
- Remote verification report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-restart-postgres-verify-report.json`
- Local restart report: `.complex-problems/L20260522-091929/artifacts/queue-restart-postgres-report.json`
- Local verification report: `.complex-problems/L20260522-091929/artifacts/queue-restart-postgres-verify-report.json`

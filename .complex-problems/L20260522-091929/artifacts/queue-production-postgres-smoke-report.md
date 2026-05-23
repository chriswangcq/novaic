# Queue Production Postgres Smoke Report

## Summary

- Status: success
- Smoke prefix: `codex-smoke-20260523T020841Z`
- Queue backend: postgres
- `/ready`: 200
- Old SQLite holders: none
- Recent log error matches after smoke marker: none

## Smoke Coverage

- Task API complete lifecycle: publish, claim, complete
- Task API fail lifecycle: publish, claim, fail without retry
- Idempotency lifecycle: acquire, complete, reacquire returns completed
- Saga safe lifecycle: create unknown smoke saga type, claim, launched, complete
- Session safe equivalent: read-only `/sessions` and `/pending` diagnostics
- Worker/outbox checks: expected processes alive and no post-marker tracebacks/errors

## Post-Smoke State Changes

- Task states changed from `done=2216, failed=10, pending=23` to `done=2217, failed=11, pending=23`
- Saga states changed from `completed=310, failed=6` to `completed=311, failed=6`
- Idempotency completed changed from 2216 to 2217
- Worker lease released changed from 2542 to 2545
- Session state remained `no_active=2`

## Process Counts

- Queue Service: 1
- Task workers: 4
- Saga workers: 2
- Session outbox worker: 1
- Saga outbox worker: 1
- Health worker: 1
- Scheduler: 1
- Business subscriber: 1
- Gateway: 1

## Artifacts

- Remote smoke report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-production-postgres-smoke-report.json`
- Local smoke report: `.complex-problems/L20260522-091929/artifacts/queue-production-postgres-smoke-report.json`
- Pool-fix restart report: `.complex-problems/L20260522-091929/artifacts/queue-restart-postgres-after-pool-fix-report.json`

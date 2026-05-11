# Deployment and Compatibility Residue Audit Result

## Summary

Deployment wiring is connected to the new service layout. Current deploy/start scripts deploy `novaic-logicalfs`, `novaic-sandbox-sdk`, `novaic-sandbox-service`, and Cortex with explicit `PYTHONPATH`/URLs. They remove retired `novaic-sandbox-core` before backend deployment.

The currently deployed backend status is healthy: all core service ports are up, and all runtime roles match expected process counts.

## Done

- Inspected root `deploy`.
- Inspected `scripts/start.sh`.
- Inspected `novaic-agent-runtime/main_novaic.py`.
- Inspected `novaic-agent-runtime/task_queue/workers/runtime_roster.py`.
- Searched for retired/fallback/compatibility strings in deploy/runtime/cortex/sandbox/logicalfs paths.
- Ran `./deploy status`.

## Verification

- `deploy` calls `remove_retired_backend_package "novaic-sandbox-core"` both in backend infra bootstrap and full services deployment.
- `deploy` syncs `novaic-sandbox-sdk`, `novaic-logicalfs`, and `novaic-sandbox-service` before restart.
- `scripts/start.sh` starts:
  - Sandboxd from `novaic-sandbox-service/main_sandbox_service.py` on port `19994`
  - Cortex with `PYTHONPATH="$BASE/novaic-cortex:$BASE/novaic-logicalfs:$BASE/novaic-sandbox-sdk:$BASE/novaic-common"`
  - Cortex with explicit `--sandboxd-url`, `--blob-service-url`, `--operational-sqlite-path`, and Redis lock args
  - Runtime workers via `runtime_roster launch-commands`
- `runtime_roster.py` is the launch/process/log single source for task/saga/outbox/health/scheduler/subscriber roles.
- `./deploy status` reported all ports healthy:
  - entangled, gateway, business, device, queue-svc, blob-service, sandboxd, cortex
- `./deploy status` reported expected runtime role counts:
  - task-worker control `2/2`
  - task-worker execution `2/2`
  - saga-worker `2/2`
  - session-outbox-worker `1/1`
  - saga-outbox-worker `1/1`
  - health `1/1`
  - scheduler `1/1`
  - subscriber `1/1`

## Known Gaps

- No deployable old `novaic-sandbox-core` path was found.
- The search found historical test/docs/lint mentions of `legacy`, `fallback`, and retired paths. Those are not current deployment wiring.
- The deploy/status command still has a generic log alias named `worker` for `task-worker-control-1.log`; this is an operator convenience label, not an old service.

## Artifacts

- This result file.
- Command evidence from `./deploy status`.

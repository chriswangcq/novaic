# P002 Check - Not Yet Complete

## Summary
P002 is improved but not complete. The canonical roster now drives supervision checks, deploy status, fresh-smoke runtime logs, CI guards, and registry mode order. However, `scripts/start.sh` still manually launches task/saga/outbox/health/scheduler processes with hand-coded loops and command blocks.

## Evidence
- SSOT exists: `novaic-agent-runtime/task_queue/workers/runtime_roster.py`.
- Shell view exists: `novaic-agent-runtime/scripts/runtime_worker_roster.py`.
- Supervision now consumes `process-checks`.
- Fresh-smoke now consumes `log-files`.
- But launch blocks in `scripts/start.sh` are still handwritten by worker type.

## Criteria Map
- One canonical roster owns worker list: partially met.
- Runtime registry imports canonical roster: met.
- Start/deploy/lint consume canonical roster: partially met; verification/status/log checks do, launch does not.
- No stale hard-coded worker roster remains in operational paths: not met for launch.

## Follow-Up Required
Make runtime worker launch generation roster-driven so `scripts/start.sh` does not carry a second process-role list.

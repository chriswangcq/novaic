# Round 009 Dispatch - Agent Runtime Team

## Objective
Operationalize diagnostics policy in stable CI and produce handoff-grade troubleshooting path.

## Mandatory Tasks
1. Ensure diagnostics policy checks run in main CI flow (not replay-only).
2. Replay idempotency unit/integration suites and attach final metrics snapshot.
3. Publish "3-step hot-key contention triage" runbook section.

## Acceptance Commands
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

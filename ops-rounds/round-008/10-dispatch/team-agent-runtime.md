# Round 008 Dispatch - Agent Runtime Team

## Objective
Harden diagnostics policy into stable operational contract.

## Mandatory Tasks
1. Promote diagnostics defaults policy to stable governance location (not runbook-only).
2. Ensure CI replay bundle enforces policy markers and fails on drift.
3. Replay idempotency unit/integration and provide final metrics snapshot.

## Acceptance Commands
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

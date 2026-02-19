# Round 003 Dispatch - Agent Runtime Team

## Objective
Close cross-process idempotency gap and turn retry visibility into proven behavior.

## Mandatory Tasks
1. Implement persistent/cross-process idempotency guard (DB or queue-level ledger/CAS).
2. Add integration test for restart + multi-worker duplicate-task scenario.
3. Update runbook from draft to final with command-backed proof.

## Acceptance Commands
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

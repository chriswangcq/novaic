# Round 004 Dispatch - Agent Runtime Team

## Objective
Hold idempotency closure and add higher-concurrency replay evidence.

## Mandatory Tasks
1. Re-run cross-process idempotency integration tests.
2. Add one higher-concurrency duplicate-task stress variant.
3. Update runbook with operational troubleshooting for ledger contention.

## Acceptance Commands
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

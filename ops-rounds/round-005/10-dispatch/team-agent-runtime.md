# Round 005 Dispatch - Agent Runtime Team

## Objective
Remove residual reliability debt by making idempotency observability and contention handling operationally actionable.

## Mandatory Tasks
1. Add lightweight diagnostics endpoint or query helper for hot idempotency keys/ledger contention.
2. Add higher-load replay case (document throughput and exactly-once outcome).
3. Add CI replay command bundle for idempotency unit + integration tests.

## Acceptance Commands
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Due / Status
- due: 2026-02-25 18:00
- status: IN_PROGRESS

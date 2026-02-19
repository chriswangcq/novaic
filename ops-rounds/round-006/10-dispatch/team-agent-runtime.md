# Round 006 Dispatch - Agent Runtime Team

## Objective
Deliver actual diagnostics capability and measurable high-load replay outcomes.

## Mandatory Tasks
1. Implement diagnostics helper/API for idempotency ledger contention visibility.
2. Execute high-load replay with throughput + exactly-once metrics summary.
3. Add CI replay command bundle (unit + integration) and verify pass.

## Acceptance Commands
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `rg "contention|diagnostics|idempotency ledger" novaic-backend -g "*.py" -g "*.md"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

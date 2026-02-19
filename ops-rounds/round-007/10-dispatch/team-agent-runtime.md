# Round 007 Dispatch - Agent Runtime Team

## Objective
Standardize diagnostics operational policy to avoid interpretation drift.

## Mandatory Tasks
1. Fix diagnostics defaults policy (limit/frequency/retention) in runbook as normative values.
2. Add one verification command/script that checks policy markers exist.
3. Replay idempotency unit + integration suite and include metrics summary.

## Acceptance Commands
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `rg "limit|frequency|retention|diagnostics" novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

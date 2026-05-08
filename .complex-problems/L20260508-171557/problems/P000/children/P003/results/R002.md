# P003 Result

## Summary

Extracted task execution branch/payload calculation into pure policy helpers. `TaskExecutionEngine` still owns protocol timing, handler invocation, metrics, and effect runner execution, but idempotency and failure/success effect plans now come from `task_execution_policies.py`.

## Changes

- Added `novaic-agent-runtime/task_queue/workers/task_execution_policies.py` with:
  - `TaskExecutionIdentity`
  - `acquire_idempotency_effect(...)`
  - `decide_idempotency_guard(...)`
  - `successful_task_plan(...)`
  - `business_error_plan(...)`
  - `retry_failure_plan(...)`
- Updated `novaic-agent-runtime/task_queue/workers/task_execution.py` to use those helpers.
- Added `novaic-agent-runtime/tests/test_pr340_task_execution_policies.py` covering:
  - acquire idempotency payload
  - completed duplicate with explicit result
  - completed duplicate with fallback dedup result
  - in-progress contention
  - acquired/continue branch
  - successful completion plan
  - business error plan
  - retryable error plan
  - exhausted retry/no-delay plan

## Verification

Executed:

```bash
pytest -q \
  tests/test_pr340_task_execution_policies.py \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/unit/task_queue/test_retry_policy_and_idempotency.py \
  tests/unit/task_queue/test_saga_worker_boundary.py \
  tests/unit/task_queue/test_dedup_guard_failure_path.py \
  tests/unit/task_queue/test_high_concurrency_retry_replay.py

PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_runtime_worker_supervision.py
```

Observed:

```text
34 passed in 0.27s
lint_runtime_worker_supervision OK
```

## Residual Risk

Saga-specific task adaptation still lives in `TaskExecutionEngine`; P004 owns saga launch/definition purity and later work can further isolate saga step payload building if needed.

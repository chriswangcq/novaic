# Round 002 Agent Runtime Package Boundary

## Target

- candidate repo: `novaic-agent-runtime`
- objective: move worker/retry/idempotency execution surface from `novaic-backend` to independently runnable package boundary

## Must-move package boundary

### Worker execution core

- `novaic-backend/task_queue/workers/task_worker_sync.py`
- `novaic-backend/task_queue/workers/saga_worker_sync.py`
- `novaic-backend/task_queue/workers/scheduler_worker_sync.py`
- `novaic-backend/task_queue/workers/health_worker_sync.py`
- `novaic-backend/task_queue/workers/watchdog_sync.py`

### Handler execution surface

- `novaic-backend/task_queue/handlers/saga_handlers.py`
- `novaic-backend/task_queue/handlers/message_handlers.py`
- `novaic-backend/task_queue/handlers/runtime_handlers.py`
- `novaic-backend/task_queue/handlers/tool_handlers.py`
- `novaic-backend/task_queue/handlers/subagent_handlers.py`
- `novaic-backend/task_queue/handlers/llm_handlers.py`
- `novaic-backend/task_queue/handlers/mcp_handlers.py`
- `novaic-backend/task_queue/handlers/context_handlers.py`
- `novaic-backend/task_queue/handlers/summary_handlers.py`
- `novaic-backend/task_queue/handlers/validation.py`

### Reliability and replay support required for operability

- `novaic-backend/task_queue/retry_policy.py`
- `novaic-backend/task_queue/client.py`
- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Boundary rules

1. Consumers integrate through stable API/contract, not direct worker module imports.
2. Any retry/idempotency semantic drift must include consumer impact note in round report.
3. Post-split candidate is valid only if replay checks still pass with unchanged command interface.

## Replayable boundary verification command

`pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`

### Expected marker

- `3 passed`

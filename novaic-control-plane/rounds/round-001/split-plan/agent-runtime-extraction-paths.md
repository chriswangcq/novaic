# Round 001 Agent Runtime Extraction Paths (Agent Runtime Team)

## Target repo

- `novaic-agent-runtime`

## Extraction scope (worker/handler modules moving out)

### Worker runtime and execution loop

- `novaic-backend/task_queue/workers/task_worker_sync.py`
  - Reason: primary task execution worker, includes retry/idempotency decision path.
- `novaic-backend/task_queue/workers/saga_worker_sync.py`
  - Reason: saga worker loop and retry semantics owned by agent runtime.
- `novaic-backend/task_queue/workers/scheduler_worker_sync.py`
  - Reason: queue scheduling and dispatch cadence for worker processing.
- `novaic-backend/task_queue/workers/health_worker_sync.py`
  - Reason: worker health loop and runtime liveness checks.
- `novaic-backend/task_queue/workers/watchdog_sync.py`
  - Reason: stuck-task/watchdog safety guard tied to worker reliability behavior.

### Handler modules (agent-runtime execution surface)

- `novaic-backend/task_queue/handlers/saga_handlers.py`
  - Reason: saga event handlers executed by agent runtime workers.
- `novaic-backend/task_queue/handlers/message_handlers.py`
  - Reason: message processing handler path used in worker execution.
- `novaic-backend/task_queue/handlers/runtime_handlers.py`
  - Reason: runtime-related queue handlers consumed by runtime and agent workers.
- `novaic-backend/task_queue/handlers/tool_handlers.py`
  - Reason: tool execution routing within worker pipeline.
- `novaic-backend/task_queue/handlers/subagent_handlers.py`
  - Reason: subagent orchestration hooks executed in worker context.
- `novaic-backend/task_queue/handlers/llm_handlers.py`
  - Reason: LLM step handlers coupled with queue worker flow.
- `novaic-backend/task_queue/handlers/mcp_handlers.py`
  - Reason: MCP step handlers coupled with queue worker flow.
- `novaic-backend/task_queue/handlers/context_handlers.py`
  - Reason: queue context assembly logic used by worker handlers.
- `novaic-backend/task_queue/handlers/summary_handlers.py`
  - Reason: summary step handlers in task pipeline.
- `novaic-backend/task_queue/handlers/validation.py`
  - Reason: handler input/state validation for worker-safe execution.

### Reliability-critical support modules that should move with workers

- `novaic-backend/task_queue/retry_policy.py`
  - Reason: unified retry policy used by task/saga workers.
- `novaic-backend/task_queue/client.py`
  - Reason: queue fail/retry API integration that carries retry delay and idempotency fields.
- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
  - Reason: operational runbook tied to worker retry/idempotency behavior.
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
  - Reason: replayable reliability baseline command bundle for post-split parity checks.
- `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - Reason: unit baseline for retry/idempotency invariants.
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - Reason: integration baseline for cross-process contention and exactly-once behavior.

## Keep outside agent-runtime repo (contract/platform ownership)

- `contracts/**`
  - Keep in shared kernel as cross-repo contract source of truth.
- `novaic-control-plane/**`
  - Keep in control-plane governance repo and reference by artifact path only.

## Consumer impact note

- Runtime/API/Desktop/Tools consumers must not import worker internals directly after split.
- Contract changes to retry/idempotency semantics require consumer impact annotation in round reports before merge.

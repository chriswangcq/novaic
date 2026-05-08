# Task Engine Effect Adapter Migration

## Problem Definition

`TaskExecutionEngine` still imports and stores concrete `TaskQueueClient`, `SagaClient`, and `BusinessClient`, then directly calls heartbeat, idempotency, complete/fail, publish, task polling, and saga lookup methods. This violates the intended boundary where action engines compute behavior and explicit effect adapters own concrete protocols.

## Proposed Solution

Add a task execution effect adapter that owns concrete task/saga/business clients and exposes an `EffectExecutor`. Refactor `TaskExecutionEngine` to use effect names for all external side effects and handler context provisioning. Keep handler invocation and deterministic protocol control in the engine, but move all client calls and URL/client context construction into the adapter.

## Acceptance Criteria

- `TaskExecutionEngine.__init__` accepts `effect_executor` instead of concrete client objects and URL strings.
- `task_execution.py` no longer imports `TaskQueueClient`, `SagaClient`, or `BusinessClient`.
- Existing task idempotency, retry, and saga-parallel behavior is preserved.
- `assemble_task_worker` wires a `TaskExecutionEffectAdapter` from concrete clients and passes its executor to the engine.
- Tests use explicit fake effect adapters instead of relying on hidden clients inside the engine.

## Verification Plan

- Run unit tests for retry/idempotency and dedup guard behavior.
- Run task worker cutover tests.
- Compile task worker modules.

## Risks

- Saga parallel publishing and polling has nested side effects; missing one effect migration would leave old code active.
- Handler context must still include the same keys expected by business handlers.

## Assumptions

- Handler context remains a dictionary because handlers currently depend on that explicit contract.
- Concrete clients are still created in worker assembly for now; later assembly DSL tickets will shrink that code.

# Task and Saga Engines Use Effect Adapters

## Problem Definition

`TaskExecutionEngine` and `SagaLaunchEngine` still own concrete protocol clients and invoke Queue/Saga/Business side effects directly. That keeps action engines in a mixed state: they compute protocol decisions and perform external effects in the same class. The target architecture requires engines to emit explicit effect calls through the generic substrate, while adapter classes own concrete clients, URLs, and protocol calls.

## Proposed Solution

Introduce task and saga effect adapters that register handlers with `EffectExecutor`. Refactor `TaskExecutionEngine` and `SagaLaunchEngine` so external operations go through `execute_effect(...)` or explicit `WorkerEffect` plans. Assemblies instantiate adapters and inject executors into engines. Tests should prove behavior is unchanged while engine modules no longer import or hold concrete client classes.

## Acceptance Criteria

- `TaskExecutionEngine` no longer imports or stores `TaskQueueClient`, `SagaClient`, or `BusinessClient`.
- `SagaLaunchEngine` no longer imports or stores `SagaClient` or `TaskQueueClient`.
- Task execution effects cover heartbeat, idempotency acquire/complete/release, complete/fail, task publish/get, saga get, and handler context provisioning.
- Saga launch effects cover heartbeat, task publish, saga mark launched, and saga mark failed.
- Worker assemblies wire concrete clients through effect adapters, not engine constructor parameters.
- Existing task/saga worker tests pass after migration.
- Boundary tests reject direct concrete-client ownership inside task/saga action engines.

## Verification Plan

- Run focused task/saga worker tests.
- Run high-concurrency idempotency/retry tests.
- Run new boundary tests for engine imports/constructor parameters.
- Compile worker modules.

## Risks

- Saga parallel steps are subtle because they publish tasks and poll task status; effect names and payloads must preserve existing retry/timeout behavior.
- Existing tests construct engines directly and need explicit test adapters to keep setup deterministic.
- Moving handler context behind an effect must not hide client dependencies; the adapter boundary should make them explicit at assembly/test construction.

## Assumptions

- Business handlers may still receive explicit context dictionaries; the gap here is moving context construction and concrete clients out of action engines.
- Source and claim objects may still own polling clients until a later assembly/source cleanup ticket; this ticket targets action engines only.

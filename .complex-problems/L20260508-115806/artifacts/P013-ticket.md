# Saga Engine Effect Adapter Migration

## Problem Definition

`SagaLaunchEngine` still imports and stores concrete `SagaClient` and `TaskQueueClient`, then directly heartbeats, publishes DAG tasks, and marks saga state. This leaves saga launch as a mixed compute/effect class instead of a pure action engine backed by explicit effect adapters.

## Proposed Solution

Add `SagaLaunchEffectAdapter` to own concrete saga/task clients and expose an `EffectExecutor`. Refactor `SagaLaunchEngine` so heartbeat, task publish, mark launched, and mark failed are all named effects. Keep DAG construction and saga launch decision flow in the engine, because that is its business/protocol computation.

## Acceptance Criteria

- `SagaLaunchEngine.__init__` accepts `effect_executor` instead of concrete clients.
- `saga_launch.py` no longer imports or stores `SagaClient` or `TaskQueueClient`.
- Saga launch publishes DAG tasks through `saga.task_publish` effects.
- Saga state transitions go through `saga.mark_launched` and `saga.mark_failed` effects.
- `assemble_saga_worker` wires a `SagaLaunchEffectAdapter`.
- Existing saga launch tests pass.

## Verification Plan

- Run saga worker cutover and saga worker boundary tests.
- Compile saga worker modules.
- Scan `saga_launch.py` for old concrete client ownership residue.

## Risks

- Existing tests assert that `mark_launched(` appears in engine source; those tests must be updated to the new architecture rather than preserving the old source-level assumption.
- Publish effect payloads must preserve DAG fields exactly.

## Assumptions

- Saga claim source may still own a saga client until the source/assembly DSL cleanup phase; this ticket targets `SagaLaunchEngine` only.

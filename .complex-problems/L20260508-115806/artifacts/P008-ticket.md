# Effect Plan Substrate Contracts

## Problem Definition

There is no shared effect-plan vocabulary for action engines to express side effects explicitly. Without this contract, engines can only call clients directly or invent local helper patterns.

## Proposed Solution

Add business-agnostic effect-plan contracts to the generic worker substrate:

- `WorkerEffect`
- `EffectPlan`
- `EffectOutcome`
- `EffectExecutor`
- `EffectExecutionError`

Export them from `queue_service.worker` and add unit tests that verify immutability, ordered execution, failure behavior, and absence of business imports.

## Acceptance Criteria

- Effect-plan contracts live in the generic worker substrate.
- The contracts are business-agnostic and do not import task/saga/session modules.
- Ordered execution and failure semantics are tested.
- No action engine is migrated in this ticket; it provides the substrate only.

## Verification Plan

- Add tests under `novaic-agent-runtime/tests`.
- Run the new test plus compile check for `queue_service/worker`.

## Risks

- Over-designing the effect contract would slow migration; keep the substrate minimal.

## Assumptions

- Synchronous effect execution is sufficient for current worker action engines.

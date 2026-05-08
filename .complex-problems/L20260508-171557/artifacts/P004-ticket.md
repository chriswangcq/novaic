# T004 Saga Launch And Definition Plan Boundary

## Problem Definition

`SagaLaunchEngine.launch(...)` still computes DAG tasks and immediately publishes them inside a direct loop, then marks the saga launched or failed inline. Saga definitions are DSL-like, but their callback hooks are not documented as explicit computation extension points.

## Proposed Solution

- Add a saga launch plan compiler that turns saga id/type/context plus a saga definition into an explicit `EffectPlan`.
- Move task-publish and mark-launched effect construction into that compiler.
- Add explicit helpers for unknown/failed saga mark-failed plans.
- Update `SagaLaunchEngine` to execute compiled plans through `EffectPlanRunner`.
- Add tests asserting plan compilation for a representative saga definition and explicit mark-failed plans.
- Add a small documentation marker for saga callback extension points.

## Verification Plan

- Run new saga plan compiler tests.
- Run existing saga worker boundary/cutover tests.
- Run effect-boundary tests to ensure engine remains behind adapters.

## Acceptance Criteria

- Saga launch can produce an explicit effect plan from saga state, definition, and context.
- Saga launch engine executes through the generic plan/effect substrate.
- Saga callback extension points are named/documented.
- Tests assert saga plan compilation and existing saga worker behavior remains green.

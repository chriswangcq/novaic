# T002 Plan-First Effect Runner Contract

## Problem Definition

Runtime action engines still own direct effect execution via `execute_effect(...)` and local `_effect(...)` helper methods. That keeps execution wiring mixed into business flow code instead of making engines emit or run explicit plans through one substrate boundary.

## Proposed Solution

- Add a reusable plan-first runner API in `novaic-agent-runtime/queue_service/worker/effects.py`.
- Migrate task, saga launch, scheduled wake, and health recovery engines away from direct `execute_effect(...)`.
- Remove local `_effect(...)` helper methods from the action engines.
- Keep existing effect handler implementations and process wiring behavior unchanged.

## Verification Plan

- Add or update tests proving `queue_service.worker` exports the runner API.
- Add boundary tests that scan action engines and fail if they import or call `execute_effect(...)` or define local `_effect(...)` helpers.
- Run targeted worker/FSM tests that exercise task execution, saga launch, scheduled wake, health recovery, and effect plans.

## Acceptance Criteria

- `queue_service.worker` exports the new runner API.
- `task_queue/workers/task_execution.py`, `saga_launch.py`, `scheduled_wake.py`, and `health_recovery.py` do not import or call `execute_effect(...)`.
- Action engines use the generic runner/substrate when invoking effects.
- Tests cover the explicit boundary and ban direct effect execution in action engines.
- Existing targeted worker/FSM tests pass.

## Non-Goals

- Do not redesign each effect payload yet.
- Do not rewrite task policy branching in this ticket; P003 owns policy tables.
- Do not change durable outbox or saga/session state schemas.

# Direct side-effect bypass cleanup

## Problem

Some queue/session/runtime paths may still create sagas, publish queue messages, or perform external side effects directly instead of routing through explicit FSM/outbox boundaries. P279 needs the direct side-effect surface classified and any high-confidence stale bypass removed or tightened.

## Success Criteria

- Direct `SagaOrchestrator.create`, `queue.publish`, and session side-effect call sites in the audited runtime/session paths are classified.
- Required adapter/outbox dispatcher boundaries are documented and retained.
- High-confidence stale bypasses are removed or replaced with explicit FSM/outbox effects.
- Ambiguous side-effect call sites are split into smaller follow-up problems.
- Focused side-effect/outbox tests pass after any source change.

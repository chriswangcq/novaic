# Emit root and wake lifecycle events

## Problem Definition

Root and wake lifecycle operations must append ContextEvents as authoritative facts. This ticket covers scope create/end paths for root initialization, wake start, and wake archive, while leaving notification attachment to P030.

## Proposed Solution

- Add API-level event writer factory with explicit clock/id providers at the Cortex boundary.
- On `/v1/scope/create`:
  - append `RootInitialized` for root scope creation/retry;
  - append `WakeStarted` for wake child scope creation/retry.
- On `/v1/scope/end`:
  - append `WakeArchived` before archiving a wake scope.
- Add focused API tests reading `context_events/events.jsonl`.
- Preserve existing idempotent scope create behavior.

## Acceptance Criteria

- Root create emits `RootInitialized`.
- Wake child create emits `WakeStarted`.
- Wake child end emits `WakeArchived`.
- Retried/idempotent create paths do not duplicate events.
- Focused tests and full Cortex tests pass.

## Verification Plan

- Add focused API event cutover tests.
- Run focused event/context tests.
- Run full `novaic-cortex` suite.

## Risks

- Root id inference from child `scope_path` must be exact.
- Archive must append event before moving/deleting active paths.

## Assumptions

- Wake scopes are identified by `skill == "wake"` at this stage.

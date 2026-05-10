# Wire context append and batch endpoints to events

## Problem Definition

Context append/batch request contracts now have optional event idempotency keys, but the endpoints still only write legacy `context.jsonl`. They must append ContextEvents first.

## Proposed Solution

- Add a small helper that classifies context messages:
  - assistant messages with `tool_calls` -> `AssistantToolCallRecorded`;
  - all other messages -> `ContextMessageAppended`.
- Wire `context_append` to append one event with optional `event_idempotency_key`.
- Wire `context_batch` to append events in message order with optional per-message keys.
- Keep transitional legacy `context.jsonl` writes until read-path/cleanup phases.
- Add focused endpoint tests.

## Acceptance Criteria

- `context_append` writes one event before transitional legacy append.
- `context_batch` writes ordered events before transitional legacy batch append.
- Assistant tool-call messages are classified as `AssistantToolCallRecorded`.
- Idempotency key retry dedupes when supplied.
- Missing idempotency keys keep identical messages distinct.
- Full Cortex tests pass.

## Verification Plan

- Add focused endpoint tests.
- Run context event/API tests.
- Run full Cortex suite.

## Risks

- Existing callers without idempotency keys can still duplicate on transport retry; this is preserved behavior and documented, not hidden.

## Assumptions

- Legacy context file output remains transitional until Phase 4/5.

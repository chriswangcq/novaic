# Cut context append and batch writes to events

## Problem Definition

`/v1/context/append` and `/v1/context/batch` still write directly to legacy `context.jsonl`. They must append ContextEvents as the authoritative message facts without collapsing distinct repeated messages or relying on hidden content hashes.

## Proposed Solution

Split the work because idempotency and endpoint wiring need explicit treatment:

- Add explicit optional event idempotency keys to context append/batch request contracts or document why a caller lacks retry idempotency.
- Wire append/batch to emit `ContextMessageAppended` or `AssistantToolCallRecorded` events before transitional legacy writes.
- Add focused tests for event stream content, message order, assistant tool-call classification, and retry behavior where keys are supplied.
- Audit remaining direct `context.jsonl` writes.

## Acceptance Criteria

- Context append emits event facts.
- Context batch emits ordered event facts.
- Distinct identical messages are not accidentally collapsed.
- When explicit idempotency keys are supplied, retries do not duplicate events.
- Existing callers remain compatible.
- Full Cortex tests pass.

## Verification Plan

- Add focused API tests.
- Run runtime caller tests if request schema changes require caller updates.
- Run full Cortex suite.

## Risks

- Using message content as idempotency key would be incorrect because two identical messages can be legitimate separate events.

## Assumptions

- Legacy `context.jsonl` remains transitional until Phase 4/5 remove read/write dependence.

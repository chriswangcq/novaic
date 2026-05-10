# Phase 3.3.2: Wire context append and batch endpoints to events

## Problem

After the idempotency contract is explicit, `/v1/context/append` and `/v1/context/batch` must append ContextEvents as authoritative facts before transitional legacy context writes.

## Success Criteria

- `context_append` appends one event for the message.
- `context_batch` appends ordered events for every message.
- Assistant messages with tool calls are recorded as `AssistantToolCallRecorded`; other messages are recorded as `ContextMessageAppended`.
- Tests verify event order and payload shape.
- Existing legacy context behavior remains green until read-path cutover.

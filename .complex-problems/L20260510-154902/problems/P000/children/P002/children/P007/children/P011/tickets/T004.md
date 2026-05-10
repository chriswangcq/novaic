# Enforce slash-free three-segment stream ids

## Problem Definition

The current ContextEvent model validates stream/root consistency by suffix only. Because `stream_id` is defined as `user_id/agent_id/root_scope_id`, delimiter ambiguity must be rejected in the schema layer before storage and idempotency rely on it.

## Proposed Solution

- Add a small helper to validate stream-id segments: non-empty string and no `/`.
- Update `build_stream_id` to use that helper for `user_id`, `agent_id`, and `root_scope_id`.
- Update `ContextEvent.validate` to parse `stream_id` into exactly three segments and require the parsed root segment to match `root_scope_id`.
- Extend focused tests for slash-containing inputs, too few segments, too many segments, empty segments, and root mismatch.

## Acceptance Criteria

- Slash-containing identity segments are rejected before building a stream id.
- Persisted event envelopes with malformed stream ids are rejected.
- Existing valid event tests still pass.
- Focused ContextEvent tests cover the new validation paths.

## Verification Plan

- Run `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py -q`.
- Inspect `novaic-cortex/novaic_cortex/context_events.py` to confirm the validation remains pure and dependency-free.

## Risks

- Overly strict validation could reject current scope ids if they legitimately contain `/`; current design and existing scope ids use slash-free ids.

## Assumptions

- Stream identity segments are IDs, not paths; `/` is reserved only as the stream key delimiter.

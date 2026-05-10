# P007 check: stream identity validation gap

## Summary

P007 made useful progress and passed focused tests, but it is not yet successful under the strict one-go check. The schema validates non-empty stream/root fields and suffix consistency, but it does not yet reject delimiter-ambiguous identity segments such as a `user_id`, `agent_id`, or `root_scope_id` containing `/`. Because stream identity is foundational to append-only ordering and idempotency, this gap should be closed before marking the schema substrate complete.

## Blocking Gaps

- `build_stream_id` validates only non-empty strings. It should reject `/` in `user_id`, `agent_id`, and `root_scope_id` because the stream key format is `user_id/agent_id/root_scope_id`.
- `ContextEvent.validate` checks only that `stream_id` ends with `/{root_scope_id}`. It should parse the stream id into exactly three non-empty slash-free segments and require the last segment to equal `root_scope_id`.
- Focused tests should cover slash-containing segments and malformed stream ids with too few or too many segments.

## Result IDs

- R001

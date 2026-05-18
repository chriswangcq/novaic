# ContextEvent append-only store audit result

## Summary

Completed the `ContextEventStore` audit. The store layer already matches the intended explicit-dependency and append-only contract; no code change was required in this slice.

## Done

- Mapped event log path ownership:
  - `novaic-cortex/novaic_cortex/context_event_store.py:42-47`
  - `event_log_path(root_scope_path)` normalizes the root scope path and stores events at `<root_scope_path>/context_events/events.jsonl`.
  - Empty root paths fail loudly with `ContextEventStoreError`.
- Mapped read behavior:
  - `novaic-cortex/novaic_cortex/context_event_store.py:49-76`
  - Missing event log returns `[]`.
  - Malformed JSON, non-object rows, and invalid ContextEvent envelopes raise `ContextEventStoreError`.
- Mapped append behavior:
  - `novaic-cortex/novaic_cortex/context_event_store.py:78-127`
  - Existing events are read first; new event sequence is `len(existing) + 1`.
  - `ContextEvent.create(...)` validates stream/root semantics.
  - Events append as JSONL through workspace `_sys_append_line`.
- Mapped explicit dependency boundary:
  - `novaic-cortex/novaic_cortex/context_event_store.py:107-118`
  - Appending requires injected `clock` and `id_provider`; there is no hidden `time` or UUID generation in this store.
- Mapped idempotency:
  - `novaic-cortex/novaic_cortex/context_event_store.py:89-105`
  - Matching idempotency key plus matching canonical semantic JSON returns the existing event without consuming providers.
  - Matching idempotency key with different semantic payload raises `ContextEventIdempotencyConflict`.
- Mapped root initialization:
  - `novaic-cortex/novaic_cortex/context_event_store.py:129-157`
  - `initialize_root(...)` builds a stable stream id and appends/reuses a `RootInitialized` event with retry-safe idempotency key `context-root:init:<stream_id>`.

## Verification

- Ran:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_store.py
```

- Result:

```text
16 passed in 0.12s
```

- Test coverage observed in `novaic-cortex/tests/test_context_event_store.py`:
  - path ownership and empty path rejection
  - missing log reads empty
  - ordered valid event read
  - malformed JSON/non-object/invalid envelope rejection
  - append requires explicit providers
  - injected event id/time fields
  - monotonic sequence assignment
  - stream/root mismatch rejection
  - root initialization without legacy migration
  - idempotent duplicate retry without provider consumption
  - idempotent conflict failure
  - non-idempotent duplicate append behavior
  - root initialization retry safety

## Known Gaps

- None for the store layer.
- Projection correctness, read-model budget behavior, runtime prepare-context handoff, and display/payload projection are intentionally out of scope and covered by sibling problems.

## Artifacts

- Source: `novaic-cortex/novaic_cortex/context_event_store.py`
- Tests: `novaic-cortex/tests/test_context_event_store.py`

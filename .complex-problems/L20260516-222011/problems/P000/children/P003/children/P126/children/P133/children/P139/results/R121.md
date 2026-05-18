# ContextEvent pure projection audit result

## Summary

Completed the pure projection audit for `project_context_events`. No code change was required in this slice. The module is deterministic from the event list, validates event replay order, projects stack/messages, and keeps tool result full payload access pointer-based through `step_ref`/`payload_ref`.

## Done

- Mapped snapshot and projection loop:
  - `novaic-cortex/novaic_cortex/context_event_projection.py:16-65`
  - Output contains `stream_id`, `root_scope_id`, `first_seq`, `applied_seq`, `messages`, `stack`, and `estimated_tokens`.
- Mapped replay invariants:
  - `novaic-cortex/novaic_cortex/context_event_projection.py:68-90`
  - First event must start at seq 1; stream/root must remain stable; sequence must be contiguous.
- Mapped root/wake/system/context/notification handlers:
  - `RootInitialized`: `context_event_projection.py:99-100`
  - `WakeStarted`: `context_event_projection.py:101-112`
  - `WakeArchived`: `context_event_projection.py:113-127`
  - `SystemPromptAdded`: `context_event_projection.py:128-129`
  - `ContextMessageAppended`: `context_event_projection.py:130-134`
  - `InputNotificationAttached`: `context_event_projection.py:135-136` and `329-347`
- Mapped skill scope behavior:
  - open: `context_event_projection.py:137-152`
  - close/LIFO/folded summaries: `context_event_projection.py:153-181`
  - active wake close summary: `context_event_projection.py:242-279`
  - stale wake/sibling suppression: `context_event_projection.py:281-326`
- Mapped tool call/result projection:
  - assistant tool calls: `context_event_projection.py:182-186`
  - tool step projection: `context_event_projection.py:187-195`
  - tool result message/metadata: `context_event_projection.py:350-380`
  - tool result text selection: `context_event_projection.py:383-392`
  - tool call id extraction: `context_event_projection.py:395-403`
- Confirmed pointer behavior:
  - `payload_ref` is stored in `_metadata`.
  - `step_ref` is preserved when present and used as stable lookup ref.
  - If `step_ref` is absent, `payload_ref` becomes the message lookup `step_ref`.
  - Tool text content is only `preview`, `summary`, `head`, or stable JSON fallback for the observation object; full payload retrieval is not performed here.
- Confirmed orphan tool result marking:
  - `context_event_projection.py:368-369`

## Verification

- Ran:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_projection.py
```

- Result:

```text
29 passed in 0.07s
```

- Test coverage observed:
  - empty snapshot
  - basic messages and applied sequence
  - invalid first seq, mixed streams, invalid sequence order
  - notification hint without fetching message body
  - wake archive and stale wake suppression
  - skill open/close, nested stack order, LIFO rejection
  - folded summaries and blank report behavior
  - stale sibling and descendant suppression
  - assistant tool call/result projection
  - multiple tool result order and payload refs
  - stable step ref when payload is externalized
  - orphan tool result marking
  - scoped tool result folding
  - missing required payload rejection

## Known Gaps

- None for pure ContextEvent projection.
- This result does not prove runtime current-vs-historical display handling, shell output formatting, or provider-native image request construction; those are covered by sibling problems.

## Artifacts

- Source: `novaic-cortex/novaic_cortex/context_event_projection.py`
- Tests: `novaic-cortex/tests/test_context_event_projection.py`

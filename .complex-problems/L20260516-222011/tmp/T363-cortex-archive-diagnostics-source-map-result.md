# Cortex Archive Diagnostics Source Map Result

## Summary

Mapped the Cortex archive persistence path for P373. The correct insertion point is `_append_wake_archived_event(...)` in `novaic-cortex/novaic_cortex/api.py`, with a writer signature extension in `novaic_cortex/context_event_writer.py`.

## Source Map

- `novaic-cortex/novaic_cortex/api.py:447-468` builds the `WakeArchived` context event by calling `ContextEventWriter.wake_archived(...)`.
- `novaic-cortex/novaic_cortex/api.py:479-495` computes the existing semantic `remaining_stack` list from active-stack projection after archive. This is for LLM context projection and must stay list-shaped.
- `novaic-cortex/novaic_cortex/api.py:656-744` calls `_append_wake_archived_event(...)` from both root and child `scope_end` paths.
- `novaic-cortex/novaic_cortex/context_event_writer.py:74-90` persists `WakeArchived` payload with `wake_scope_id`, semantic `reason`, and semantic `remaining_stack`.
- `novaic-cortex/novaic_cortex/context_event_projection.py:113-119` consumes `WakeArchived.payload.remaining_stack` as a list and reconstructs context stack from it. Therefore diagnostic `remaining_stack` must not replace this field.

## Recommended Contract Shape

Persist runtime finalize diagnostics as a nested `archive_diagnostics` object inside the `WakeArchived` payload only when the request supplies diagnostics:

```json
{
  "wake_scope_id": "wake-1",
  "reason": "scope_end_child",
  "remaining_stack": [],
  "archive_diagnostics": {
    "session_generation": 7,
    "finalize_reason": "reply_no_followup",
    "remaining_stack": {"known": true, "depth": 0, "frames": []},
    "round_num": 3
  }
}
```

This avoids conflating two meanings:

- `remaining_stack` at payload top level: semantic post-archive stack list used by context projection.
- `archive_diagnostics.remaining_stack`: runtime finalize snapshot dict used for audit/recovery.

## Tests To Add Or Update

- Add a Cortex test where `scope_end(ScopeEndRequest(...diagnostics...))` archives a wake and asserts the final `WakeArchived` payload contains `archive_diagnostics` exactly.
- Keep existing structural tests unchanged to prove no-diagnostics callers still produce the legacy-neutral payload.
- Reuse `test_scope_end_request_validates_archive_diagnostics_contract` for invalid diagnostic request validation.

## Residual Risk

None at source-map level. Implementation still needs to add the nested diagnostics object and focused tests.

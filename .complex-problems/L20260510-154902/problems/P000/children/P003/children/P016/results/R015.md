# Projection tool placement result

## Summary

Implemented assistant tool call and tool step projection in the pure ContextEvent projector. Tool results now render as deterministic `role=tool` messages using explicit observation fields and metadata, without reading payload bytes or legacy step files.

## Done

- Added projection for `AssistantToolCallRecorded`.
- Added projection for `ToolStepRecorded`.
- Tracked observed tool call ids to mark orphan tool results.
- Rendered tool result content from `observation.preview`, `observation.summary`, `observation.head`, or stable JSON.
- Preserved `call_id`, `tool`, `status`, and `payload_ref` in metadata.
- Added tests for assistant call + result, multiple tools, orphan result, payload_ref preservation, and scoped tool result folding.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 63 passed.
- Static scan found no Workspace/file/legacy DFS/payload/env/time/id dependency in `context_event_projection.py`.

## Known Gaps

- None for tool projection.
- Phase 2 verification/non-cutover audit remains open in P017.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`

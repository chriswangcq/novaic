# Projection snapshot/message result

## Summary

Implemented the first pure ContextEvent projector layer. It accepts ordered events and returns a deterministic snapshot with root id, applied seq, messages, stack, and estimated token count for basic root/wake/message/notification events.

## Done

- Added `novaic-cortex/novaic_cortex/context_event_projection.py`.
- Added `ContextProjectionSnapshot`, `ContextEventProjectionError`, and `project_context_events`.
- Implemented projection for:
  - `RootInitialized`;
  - `WakeStarted`;
  - `WakeArchived`;
  - `SystemPromptAdded`;
  - `ContextMessageAppended`;
  - `InputNotificationAttached`.
- Added tests in `novaic-cortex/tests/test_context_event_projection.py`.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py tests/test_context_event_store.py tests/test_context_event_projection.py -q` passed: 49 passed.
- Static scan found no Workspace/file/legacy DFS/payload/env/time/id dependency in the projector.
- Static scan found `im_read` only inside the literal environment notification hint text, not as an IM call or hidden dependency.

## Known Gaps

- Skill scope fold semantics remain open in P015.
- Tool call/result placement remains open in P016.
- Endpoint/read-path cutover remains open in later phases.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`

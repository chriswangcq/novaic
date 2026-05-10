# Write-path map and ContextEvent writer boundary completed

## Summary

Added the Phase 3 write-path map and a `ContextEventWriter` boundary around `ContextEventStore`. The writer keeps per-request identity explicit through `ContextEventWriteContext` and still relies on the store's injected clock/id providers, so it does not introduce hidden time/id/env inputs.

## Done

- Added `docs/cortex/context-event-write-cutover-map.md`.
- Linked the map from `docs/cortex/README.md`.
- Added `novaic-cortex/novaic_cortex/context_event_writer.py`.
- Added `ContextEventWriteContext` with explicit:
  - `user_id`;
  - `agent_id`;
  - `root_scope_id`;
  - `root_scope_path`;
  - `actor`.
- Added `ContextEventWriter` helpers for:
  - `RootInitialized`;
  - `WakeStarted`;
  - `WakeArchived`;
  - `SystemPromptAdded`;
  - `ContextMessageAppended`;
  - `InputNotificationAttached`;
  - `SkillScopeOpened`;
  - `SkillScopeClosed`;
  - `AssistantToolCallRecorded`;
  - `ToolStepRecorded`.
- Added `novaic-cortex/tests/test_context_event_writer.py`.

## Verification

- Focused writer/projection/model/store tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_writer.py tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_context_event_store.py -q`
  - Result: `73 passed in 0.11s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `428 passed in 0.71s`
- Static scan confirmed current API/runtime/workspace/context-stack modules do not import `ContextEventWriter` yet.
- Static scan confirmed `context_event_writer.py` has no `uuid`, `time.`, `os.environ`, `datetime.now`, or `utcnow` usage.

## Residual Risk

- This ticket deliberately does not cut live endpoints over. P024-P028 own the actual endpoint migration and legacy write cleanup.

## Artifacts

- `docs/cortex/context-event-write-cutover-map.md`
- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/tests/test_context_event_writer.py`

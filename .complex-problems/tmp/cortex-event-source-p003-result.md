# Phase 2 projection and replay completed

## Summary

Phase 2 completed the pure ContextEvent projection layer. The projector can replay an ordered event stream into LLM-facing messages, active stack frames, folded summaries, notification hints, and tool result placement without reading Workspace files, payload bytes, legacy `context.jsonl`, legacy step indexes, env, clocks, or ids. This phase intentionally stops before write-path/read-path cutover.

## Done

- P014 / R009 added the projection snapshot and basic message events:
  - `RootInitialized`
  - `WakeStarted`
  - `WakeArchived`
  - `SystemPromptAdded`
  - `ContextMessageAppended`
  - `InputNotificationAttached`
- P015 / R014 completed scope stack and fold semantics:
  - skill open/close frames;
  - nested stack order;
  - LIFO validation;
  - fold rendering;
  - blank structural close pass-through;
  - nested folds;
  - stale open sibling and descendant suppression.
- P016 / R015 completed tool call/result placement:
  - `AssistantToolCallRecorded`
  - `ToolStepRecorded`
  - deterministic `role=tool` messages;
  - orphan tool result marking;
  - explicit `payload_ref` metadata preservation without payload reads.
- P017 / R016 verified Phase 2 boundaries:
  - focused event-source tests pass;
  - existing ContextEngine tests pass;
  - full Cortex suite passes;
  - static scans confirm no hidden projector IO/time/env/payload dependencies;
  - static scans confirm no accidental endpoint/read-path cutover.

## Verification

- Focused event-source tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_context_event_store.py -q`
  - Latest result: `63 passed in 0.10s`
- Existing ContextEngine/context tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_pr84_minimal_structure_invariants.py tests/test_pr234_control_stack.py tests/test_context_engine_dfs.py tests/test_pr73_folded_scope_rendering.py tests/test_pr66_system_scope_rendering.py -q`
  - Latest result: `29 passed in 0.34s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Latest result: `418 passed in 0.61s`
- Static boundary scans:
  - Forbidden projector dependency scan returned no matches.
  - API/runtime/workspace/context-stack projector-reference scan returned no matches.

## Known Gaps

- Phase 3 must emit ContextEvents from the live write paths.
- Phase 4 must cut prepare/read paths over to event replay.
- Phase 5 must delete/reset old data and remove legacy projection writers/readers.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`

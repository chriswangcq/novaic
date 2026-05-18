# ContextEvent projection and read-model cleanup result

## Summary

P422 found and fixed a real projection leak risk: when a tool observation dict had no `preview`, `summary`, or `head`, ContextEvent projection serialized the entire observation into LLM history. That could re-inline display/media/base64-shaped payloads. The fallback now emits a bounded pointer-style diagnostic using `payload_ref` and observation keys instead of serializing the observation body.

## Done

- Inspected:
  - `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `novaic-cortex/novaic_cortex/context_event_read_model.py`
- Added pointer-oriented fallback behavior in `_tool_result_content()`.
- Added regression coverage for unknown display/image-shaped observations.
- Ran focused projection/read-model/payload projection tests.
- Saved pre/post guard artifacts.

## Code Changes

- `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `_tool_result_content()` now accepts `payload_ref`.
  - Unknown dict observations no longer call `stable_json(observation)`.
  - Unknown dict observations now return:
    - `"[Tool result omitted from context; inspect payload_ref=...; keys=...]"`
    - or a no-ref omitted diagnostic.
- `novaic-cortex/tests/test_context_event_projection.py`
  - Added `test_project_context_events_unknown_tool_observation_does_not_inline_payload`.

## Verification

- Focused tests:
  - `tests/test_context_event_projection.py`
  - `tests/test_context_event_read_model.py`
  - `tests/test_context_event_read_source_guards.py`
  - `tests/test_tool_output_projection.py`
  - Result: `53 passed in 0.13s`.
- Post-fix guard confirms `stable_json(observation)` is no longer present and projection uses the pointer-style omitted diagnostic.

## Known Gaps

This fixes projection/read-model fallback leakage. Workspace step payload normalization and display/current-step projection remain separate P417 child work.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p422/context_event_projection.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p422/context_event_read_model.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p422/payload-projection-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p422/post-fix-payload-projection-guard.txt`

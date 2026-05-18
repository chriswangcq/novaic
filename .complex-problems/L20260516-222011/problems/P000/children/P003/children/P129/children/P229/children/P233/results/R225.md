# Result: runtime LLM context expansion avoids full payload reads

## Summary

Runtime LLM context expansion uses Cortex formatted step projection by default, not full payload read APIs. `prepare_llm_call` injects an explicit preprocessing pipeline, `expand_messages_for_llm` requires `step_ref`, computes `history`/`current_tool_result`/`display_perception` projections, and calls `CortexBridge.read_step_formatted` (`/v1/steps/read_formatted`). Runtime searches show no default context path using `/v1/payload/read`; payload tools exist only as explicit shell/CLI surface.

## Done

- Mapped `prepare_llm_call` context expansion pipeline.
- Mapped `expand_messages_for_llm`, projection selection, and `fetch_step_for_llm`.
- Mapped `CortexBridge.read_step_formatted` endpoint use.
- Searched runtime for payload read/search API usage in default context paths.
- Ran focused runtime tests for step-ref expansion, projection selection, display history handling, and explicit preprocessing dependencies.

## Verification

- Code evidence: `novaic-agent-runtime/task_queue/contracts/llm_call.py:115-145` calls injected `expand_messages_for_llm`, then `sanitize_context`, then `process_multimodal_messages`.
- Code evidence: `novaic-agent-runtime/task_queue/utils/step_result_client.py:20-63` resolves tool results through `bridge.read_step_formatted`, requiring `tool_call_id` and passing `step_ref`.
- Code evidence: `novaic-agent-runtime/task_queue/utils/step_result_client.py:119-212` requires `step_ref`, selects projection, and replaces inline content with formatted step content.
- Code evidence: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:424-447` posts to `/v1/steps/read_formatted`, not `/v1/payload/read`.
- Search evidence: runtime `rg` found `/v1/payload` only as explicit payload tools in `tool_surface_policy.py`, not in default LLM context expansion.
- Test evidence: `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:133-410` covers required `step_ref`, formatted Cortex resolution, step_ref pass-through, display projection gating, history projection, and old-display reinjection prevention.
- Test evidence: `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:185-275` covers prepare-LLM-call display image insertion and non-display image rejection.
- Test command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.
- Test result: `36 passed in 0.15s`.

## Known Gaps

- Explicit payload CLI/tool exposure is still covered by `P230`.
- Provider-specific image request conversion is outside the default context expansion boundary and was covered earlier in factory tests.

## Artifacts

- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`

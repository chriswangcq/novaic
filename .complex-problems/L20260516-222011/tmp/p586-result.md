# BlobRef-backed display perception implementation result

## Summary

Implemented BlobRef-backed display perception end to end across the local runtime/Cortex request assembly path. Display durable payloads no longer persist image base64; Cortex preserves BlobRef media references; runtime resolves current-round display refs into image MCP content only for `display_perception`; focused cleanup found no active durable-base64 residue in the display surface.

## Child Results

- `P588` / `R570` + `R571`: runtime display durable payload is BlobRef-only.
  - Follow-up `P592` fixed the hidden inline-byte dependency so durable image refs derive from Blob metadata, not `_mcp_content[].data`.
- `P589` / `R572`: Cortex projection recognizes `image_ref` and emits BlobRef-backed `image_ref` for display perception while history remains text-only.
- `P590` / `R573`: runtime step-ref expansion resolves current-round display `image_ref` through Blob Service and converts it to image MCP content for the existing multimodal pipeline.
- `P591` / `R574`: focused display cleanup/regression tests passed and no active durable-base64 expectations remained in the checked display surface.

## Code Areas Changed

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`

## Verification

- Runtime display handler tests: passed.
- Runtime historical image injection tests: passed.
- Runtime selected resolver tests: passed.
- Cortex projection tests: passed.
- Related boundary tests for factory multimodal/tool surface/runtime path/shell blob contract: passed.
- Search audit found no suspicious durable-base64 matches in the checked display path.

## Residual Risk

This closes the implementation problem. The next child problem should still perform final verification (`P587`) and decide whether unrelated session-generation test failures need a separate follow-up outside this display-perception scope.

# Runtime current display image-ref resolver result

## Summary

Implemented the runtime current-round resolver for Cortex `image_ref` display perception output. Runtime now resolves `image_ref` BlobRefs only when expanding a tool step with projection `display_perception`, replacing references with image MCP content before the existing multimodal conversion step.

## Code Changes

- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - Added BlobRef image-ref resolution for `display_perception` only.
  - Fetches Blob Service using tenant header `X-Tenant-ID`.
  - Replaces `image_ref` with `{"type":"image","data":...,"mimeType":...}` only in the current LLM request path.
  - Converts missing/failed/oversized/non-image BlobRefs into bounded text diagnostics.
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
  - Added tests proving current display image refs resolve to image MCP content.
  - Added tests proving history image refs do not fetch Blob Service.
  - Added a failure fallback test for missing BlobRefs.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - Updated stale durable-base64 expectations.
  - Current display perception tests now use BlobRef `image_ref` plus runtime resolver.
  - History replay still proves old display output does not inject images.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python -m pytest novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_resolves_current_display_image_ref novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_does_not_resolve_history_image_ref novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_image_ref_fetch_failure_becomes_text novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_uses_display_projection_only_for_display_tool novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py -q`
  - Passed: `15 passed in 0.06s`.
- A broader run of the whole `test_pr71_no_tool_retry_context_cleanup.py` file still has unrelated pre-existing `session_generation` failures in tests outside this display resolver scope.

## Residual Risk

The resolver is wired for current display perception, but the remaining testing/cleanup child should run broader searches and reconcile any remaining stale test assumptions or unrelated focused-test failures.

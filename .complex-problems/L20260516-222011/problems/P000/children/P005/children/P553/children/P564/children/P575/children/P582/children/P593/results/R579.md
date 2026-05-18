# Result: Current display image injection tests inventoried

## Summary

Current-round display image injection has direct regression coverage. Tests prove that current `display` tool messages select `display_perception`, BlobRef `image_ref` content is fetched from Blob Service with tenant headers, and the resolved provider-facing payload contains image MCP content.

## Done

- Recorded test inventory scan output in `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-scan.txt`.
- Scan command recorded:
  - `rg -n "display_perception|image_ref|prepare_llm_call_without_retry|latest_tool_call_ids|display:2|display tool" novaic-agent-runtime/tests -S`
  - `nl -ba ... | sed -n ...` slices for the cited runtime tests.
- Cited `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:213-243`, which checks projection selection: current display uses `display_perception`; non-display remains `current_tool_result`.
- Cited `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:246-313`, which checks current display `image_ref` BlobRef resolution to MCP image content.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:215-312`, which checks `prepare_llm_call` injects the display image before a following system/active-stack message.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python -m pytest novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_uses_display_projection_only_for_display_tool novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_resolves_current_display_image_ref novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_prepare_llm_call_injects_display_step_image_before_following_system -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-tests.txt`.
- Outcome: `3 passed in 0.07s`.

## Known Gaps

- None for current-round display image injection. This child does not cover historical replay or durable base64 absence; those are separate P582 children.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-tests.txt`

# Media-Like Shell Stdout Regression Result

## Summary

Added focused regression coverage for screenshot-like `/9j/` shell stdout. The tests prove shell output remains bounded terminal text and Cortex does not project shell raw payloads as display images.

## Done

- Updated `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`.
  - Added `test_shell_media_like_stdout_stays_bounded_terminal_text`.
  - The test simulates a large JPEG-like base64 stdout string.
  - It asserts public shell output is `tool-output.v1`, bounded, truncated, has no `_mcp_content`, and contains no `data:image/` text.
- Updated `novaic-cortex/tests/test_tool_output_projection.py`.
  - Added `test_media_like_shell_step_payload_does_not_project_as_display_image`.
  - The test verifies `tool-step-payload.v1` shell raw stdout is not projected into display/image content.

## Verification

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_shell_output_contract.py`
  - Passed: `6 passed`.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_tool_output_projection.py tests/test_step_result_projection.py`
  - Passed: `15 passed`.

## Known Gaps

- No known gap for this regression slice.

## Artifacts

- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-cortex/tests/test_tool_output_projection.py`

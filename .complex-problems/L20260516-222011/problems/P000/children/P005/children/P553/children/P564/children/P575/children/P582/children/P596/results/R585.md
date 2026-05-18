# Result: Active-stack display ordering tests inventoried

## Summary

Active-stack/system-message display ordering has direct regression coverage. Tests prove a current display result remains `display_perception` even when a system/active-stack message follows it, while non-current display messages fall back to `history`.

## Done

- Recorded scan output in `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-scan.txt`.
- Scan command recorded:
  - `rg -n 'Active skill stack|system message follows|latest_tool_call_ids|current_round|history.*display|display_perception|round-old|round-current' novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py -S`
  - `nl -ba ... | sed -n ...` slices for ordering tests.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:215-323`, which checks current display image injection remains before a following active-stack system message.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:324-462`, which checks mixed shell/display replay uses `history` for old shell and `display_perception` for current display.
- Cited `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:457-496`, which checks display projection can be inferred from the assistant tool call.
- Cited `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:499-557`, which checks old display is not re-injected after a newer tool block.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_prepare_llm_call_injects_display_step_image_before_following_system novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_screenshot_artifact_manifest_display_current_then_history_replay novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_infers_display_projection_from_assistant_tool_call novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_does_not_reinject_old_display_after_new_tool_block -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-tests.txt`.
- Outcome: `4 passed in 0.05s`.

## Known Gaps

- None for active-stack/system-message display ordering coverage.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-tests.txt`

# Result: Historical display replay tests inventoried

## Summary

Historical display replay has direct regression coverage. Tests prove old display image refs use `history` projection, do not fetch Blob bytes, and do not create provider image/user-image messages during normal history replay.

## Done

- Recorded test inventory scan output in `.complex-problems/L20260516-222011/tmp/p594/history-replay-scan.txt`.
- Scan command recorded:
  - `rg -n 'history.*display|display.*history|does_not_resolve_history|history must not fetch|\\[call\\["projection"\\] for call in calls\\]' novaic-agent-runtime/tests -S`
  - `nl -ba ... | sed -n ...` slices for the cited runtime tests.
- Cited `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:316-359`, which asserts historical display uses `history` projection and makes Blob fetching fail the test.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:340-462`, which checks a screenshot shell step replays as `history` while current display uses `display_perception`.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:36-45`, which checks a history-projected display image does not create a user image message.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python -m pytest novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_does_not_resolve_history_image_ref novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_screenshot_artifact_manifest_display_current_then_history_replay novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_history_projection_marker_is_stripped_without_image_injection -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p594/history-replay-tests.txt`.
- Outcome: `3 passed in 0.05s`.

## Known Gaps

- None for historical display replay. Durable base64 absence and active-stack ordering have sibling child problems.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p594/history-replay-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p594/history-replay-tests.txt`

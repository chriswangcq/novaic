# Active-stack ordering display media result

## Summary

Verified active-stack/system-message ordering does not suppress current display media under the current in-repo contract. The prepared message order includes the generated provider image user message before the following system message, and the display tool result is sanitized with a placeholder rather than image bytes.

## Done

- Ran the targeted runtime test file covering current display projection and historical image suppression.
- Captured the assertion slice for the active-stack-following-display case.

## Verification

- Command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`.
- Result: `9 passed in 0.08s`.
- Assertion evidence: `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:203-262` verifies:
  - Cortex formatted read uses `display_perception`.
  - Prepared roles are `assistant`, `tool`, `user`, `system`.
  - Tool payload image item is a placeholder and has no `data`.
  - Generated user message contains `image_url` with data URL.
  - Following system message remains present.

## Known Gaps

- No in-repo ordering gap found. If a future provider requires system messages before all user media, that would be a separate provider-contract design change, not a current regression.

## Artifacts

- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`

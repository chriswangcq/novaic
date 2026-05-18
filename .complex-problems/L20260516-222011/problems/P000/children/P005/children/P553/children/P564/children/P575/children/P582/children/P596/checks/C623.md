# Check: Active-stack display ordering coverage is direct

## Summary

Success. `R585` directly covers the ordering failure mode: a following active-stack/system message does not prevent current display perception, and older display output is correctly downgraded to history.

## Evidence

- `R585` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p596/active-stack-ordering-tests.txt`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:215-323` proves display image injection happens before the following system message.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:324-462` proves old shell/display replay plus current display ordering uses `["history", "display_perception"]`.
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:457-496` proves display projection can be inferred from assistant tool call metadata.
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:499-557` proves old display is not re-injected after a newer tool block.

## Criteria Map

- Exact scans recorded: satisfied.
- Current display before following system message: satisfied.
- Non-current display fallback to history: satisfied.
- Follow-up if missing: not needed.
- Belongs under P582 split: satisfied; this child covers ordering only.

## Execution Map

- `T591` executed read-only inventory plus focused pytest.
- Focused command passed: `4 passed in 0.05s`.
- No code changes were needed.

## Stress Test

- Plausible failure mode: the system active-stack message becomes the apparent last context item and causes the preceding display tool result to miss current-round image injection.
- Covered by `test_prepare_llm_call_injects_display_step_image_before_following_system`, which asserts the prepared message order is assistant, tool, injected user image, then system.

## Residual Risk

- None for the ordering contract under test.

## Result IDs

- R585

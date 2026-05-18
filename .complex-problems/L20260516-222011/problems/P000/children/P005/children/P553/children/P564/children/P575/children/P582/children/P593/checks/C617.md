# Check: Current display image injection coverage is direct

## Summary

Success. `R579` proves the current-round display image-injection path has direct tests for both projection selection and BlobRef-to-image resolution, including the active-stack/system-message ordering case.

## Evidence

- `R579` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p593/current-display-injection-tests.txt`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:213-243` verifies current display selects `display_perception`.
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py:246-313` verifies `image_ref` BlobRef fetch and provider-facing image MCP content.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:215-312` verifies `prepare_llm_call` injects the image before a following system message.

## Criteria Map

- Exact scan/test commands recorded: satisfied in `R579`.
- Cites runtime tests for `display_perception`: satisfied by PR71 test lines 213-243.
- Cites runtime tests for `image_ref` resolution: satisfied by PR71 test lines 246-313.
- Follow-up if missing: not needed; direct coverage exists.
- Belongs under P582 split: satisfied; this verifies only current display injection while siblings cover history/durable/order inventory.

## Execution Map

- `T585` ran a read-only test inventory plus focused pytest.
- Focused command passed: `3 passed in 0.07s`.
- No code changes were needed for this child problem.

## Stress Test

- Plausible failure mode: a system/active-stack message after the display tool result causes the runtime to miss the current display image and leave only a text receipt.
- Covered by `test_prepare_llm_call_injects_display_step_image_before_following_system`, which asserts the resulting role order includes the injected user image before the following system message.

## Residual Risk

- This child does not prove historical replay or durable-base64 absence; those are separate sibling children and remain in the ledger.

## Result IDs

- R579

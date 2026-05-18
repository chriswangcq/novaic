# Check: Display handler durable ImageRef coverage is direct

## Summary

Success. `R582` directly covers display handler durable media safety: public tool content strips inline data, durable payload stores BlobRef `image_ref`/`display_files`, and oversized image handling does not depend on inline bytes.

## Evidence

- `R582` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p598/display-durable-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p598/display-durable-tests.txt`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:65-120` proves public display output uses placeholders and durable payload stores `image_ref` plus `display_files`.
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:123-156` proves durable `image_ref` does not depend on inline image data.
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:167-212` proves `_ok` persists references rather than media bytes.

## Criteria Map

- Exact scans recorded: satisfied.
- Public placeholder/no-data coverage cited: satisfied.
- Durable `image_ref` and `display_files` coverage cited: satisfied.
- Inline-byte independence coverage cited: satisfied.
- Follow-up if missing: not needed.

## Execution Map

- `T589` executed a read-only inventory and focused pytest.
- Focused command passed: `3 passed in 0.05s`.
- No code changes were needed.

## Stress Test

- Plausible failure mode: display fetches image bytes and `_ok` persists the same base64 in durable `llm_content`.
- Covered by tests that assert `"data"` and concrete base64 are absent from public/durable payload while `image_ref` metadata remains.

## Residual Risk

- This child covers the display handler only. Cortex projection behavior remains in sibling P599.

## Result IDs

- R582

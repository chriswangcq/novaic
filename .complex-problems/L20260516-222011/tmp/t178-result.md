# Runtime current display selection and active-stack ordering result

## Summary

Closed the runtime side of current display handling by completing child problems P192 and P193. Runtime selects `display_perception` for current display steps, avoids stale display reinjection, and preserves current display media even when the active-stack system message follows the display tool result.

## Done

- P192 verified step-ref projection selection:
  - current `display` -> `display_perception`;
  - old display -> `history`;
  - current shell/non-display -> `current_tool_result`.
- P193 verified active-stack-after-display media preservation:
  - `_projection` survives sanitization until multimodal conversion;
  - display tool content becomes placeholder-only;
  - image data becomes a separate user image message;
  - following system active-stack message remains in order.

## Verification

- P192 checks passed:
  - `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`: `14 passed in 0.08s`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`: `9 passed in 0.08s`
- P193 checks passed:
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`: `9 passed in 0.08s`

## Known Gaps

- Provider-specific final request schema remains P190.
- End-to-end screenshot/display regression remains P191.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/t179-result.md`
- `.complex-problems/L20260516-222011/tmp/p192-check.md`
- `.complex-problems/L20260516-222011/tmp/t180-result.md`
- `.complex-problems/L20260516-222011/tmp/p193-check.md`

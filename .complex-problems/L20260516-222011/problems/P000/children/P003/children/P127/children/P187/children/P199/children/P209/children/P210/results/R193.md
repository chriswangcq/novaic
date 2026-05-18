# Nested `result` wrapper branch audit result

## Summary

Removed the generic nested `result` unwrapping branch from `parse_tool_result`. Current durable projection uses `tool-step-payload.v1 -> llm_content`; generic `result` unwrapping had no current production writer evidence and could revive old wrapped image payloads.

## Code Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - Removed the branch that rewrote `raw = raw["result"]` for any dict containing a nested `result`.
- `novaic-cortex/tests/test_tool_output_projection.py`
  - Added `test_nested_result_wrapper_stays_text_and_does_not_project_image`.

## Verification

- Branch search:
  - `rg -n "result.*raw = raw|解包嵌套|raw\\[\\\"result\\\"\\]|nested_result_wrapper|tool-step-payload.v1" novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/tests/test_tool_output_projection.py -S`
  - Result: no nested unwrap branch remains; only `tool-step-payload.v1` and the new regression test are present.
- Focused tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `16 passed in 0.08s`.

## Branch Decision

Removed rather than retained. Reason: the branch was broad, implicit compatibility, not tied to a current writer, and could turn old wrapped `_mcp_content` image payloads into display files. Unknown/wrapped dicts now fall through to text JSON serialization, which is safer and inspectable.

## Residual Risk

Very old persisted payloads shaped as `{"result": {"text": "..."}}` will now appear as JSON text instead of extracted text. That is acceptable because it avoids implicit compatibility that can re-enable image/media injection.

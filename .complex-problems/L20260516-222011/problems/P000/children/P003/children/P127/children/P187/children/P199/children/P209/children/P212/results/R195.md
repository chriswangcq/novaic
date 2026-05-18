# Generic dict JSON fallback audit result

## Summary

Retained the unknown-dict fallback as diagnostic text, but made it explicitly labeled and bounded. Unknown payloads can no longer flood LLM context with arbitrarily large JSON/base64-like strings through this fallback.

## Code Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - Added `_UNKNOWN_DICT_TEXT_LIMIT = 2_000`.
  - Labeled unknown dict fallback as `[Unknown tool result JSON]`.
  - Truncated unknown JSON text before returning parsed text.
- `novaic-cortex/tests/test_step_result_projection.py`
  - Strengthened unserializable-object test to assert text-only fallback label.
  - Added `test_parse_tool_result_unknown_dict_fallback_is_bounded_text_only`.

## Verification

- Focused tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `18 passed in 0.06s`.
- Smoke check:
  - Small unknown dict returns `[Unknown tool result JSON]` and no display files.
  - Large unknown dict returns bounded text length `2083` and includes `Truncated unknown tool result JSON`.

## Branch Decision

Retained in narrowed form. Reason: unknown dicts are still useful diagnostic text, but they are not a business projection contract and must not be unbounded.

## Residual Risk

Detailed unknown diagnostic payloads may be truncated. Full raw payload inspection remains the intended path for large outputs.

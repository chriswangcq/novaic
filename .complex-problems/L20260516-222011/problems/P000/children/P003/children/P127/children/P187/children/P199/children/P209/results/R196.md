# Retained production projection branch audit parent result

## Summary

Completed retained projection branch audit. One broad compatibility branch was removed, one active display-perception branch was retained with stronger tests, and one generic fallback was narrowed to bounded diagnostic text.

## Child Results

- `R193` / `P210`: Removed generic nested `result` unwrapping and added regression coverage proving wrapped images stay inert text.
- `R194` / `P211`: Retained MCP image/data-url parsing only for explicit `display_perception`, with tests proving history/current-tool projections stay text-only.
- `R195` / `P212`: Retained unknown-dict fallback only as labeled, bounded diagnostic text.

## Branch Decisions

- Removed:
  - Generic nested `result` unwrapping in `parse_tool_result`.
- Retained with explicit rationale:
  - MCP image/data-url parsing and display image formatting, because current explicit display perception still needs it.
- Narrowed:
  - Generic dict JSON fallback now has `_UNKNOWN_DICT_TEXT_LIMIT = 2_000` and a diagnostic label.

## Verification

Each child ran focused Cortex projection tests after its edits. The final child test run covered:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py
```

Result: `18 passed in 0.06s`.

## Code Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`

## Residual Risk

Runtime routing must continue to request `display_perception` only for explicit display results. That boundary is outside this Cortex branch audit and is covered by runtime projection tests.

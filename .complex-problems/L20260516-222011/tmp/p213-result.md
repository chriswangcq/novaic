# Stale `resolve_for_llm` test deletion result

## Summary

Deleted `novaic-cortex/tests/test_resolve_for_llm.py`, the stale test file for the removed `resolve_for_llm` API and obsolete inline-image behavior.

## Code Changes

- Deleted `novaic-cortex/tests/test_resolve_for_llm.py`.

## Verification

- Reference check:
  - `rg -n "resolve_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests novaic-agent-runtime novaic-llm-factory novaic-common -S || true`
  - Result: no output.
- Focused Cortex projection tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `18 passed in 0.07s`.

## Residual Risk

None for the stale test deletion. Broader projection regression remains in sibling problems.

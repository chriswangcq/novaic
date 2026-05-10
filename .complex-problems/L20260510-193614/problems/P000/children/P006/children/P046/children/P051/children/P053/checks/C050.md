# Phase 5B3.2 Step Projection Explicit API Cutover Check

## Summary

Success. Result `R047` completes the explicit API cutover: the `format_for_llm` compatibility wrapper and package export are gone, direct Cortex/sibling references are absent, and projection behavior is tested through explicit APIs.

## Evidence

- `R047` deleted `format_for_llm` from `step_result_projection.py`.
- `R047` removed `format_for_llm` from `novaic_cortex.__init__` import/export.
- Static searches for `format_for_llm` in Cortex source/tests and sibling packages returned no matches.
- Targeted projection tests passed: `20 passed in 0.11s`.
- Py compile passed for changed modules plus `api.py`.

## Criteria Map

- No `format_for_llm` function in `step_result_projection.py`: satisfied by deletion and static search.
- No package import/export in `__init__.py`: satisfied by deletion and static search.
- No Cortex source/test imports: satisfied by static search.
- Explicit projection behavior remains covered: satisfied by updated `test_step_result_projection.py` and `test_tool_output_projection.py`.
- Targeted projection tests pass: satisfied.

## Execution Map

- The implementation was limited to the wrapper/export removal and direct test cutover.
- It did not rename all remaining `legacy` wording; that remains correctly scoped to P054.

## Stress Test

- The search included sibling packages, not only Cortex, reducing the chance of hidden workspace imports.
- The tests cover both history truncation and display-perception data-url behavior after wrapper deletion.

## Residual Risk

- `/v1/steps/read_formatted` still has an `include_display` request-field fallback for unknown/empty `projection`. It no longer relies on `format_for_llm`; P055 should classify whether this is an intentional current API adapter or needs a follow-up.

## Result IDs

- R047

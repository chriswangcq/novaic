# Projection test residue cleanup parent result

## Summary

Completed projection test residue cleanup. Deleted stale `resolve_for_llm` tests, renamed misleading guard tests, and verified focused Cortex/runtime/factory projection suites.

## Child Results

- `R198` / `P213`: Deleted `novaic-cortex/tests/test_resolve_for_llm.py`; no active `resolve_for_llm` references remain.
- `R199` / `P214`: Renamed misleading projection guard tests and fixture wording from legacy/old to unsupported/guard language.
- `R200` / `P215`: Ran focused projection cleanup verification across Cortex, runtime, and factory/log tests.

## Code/Test Changes

- Deleted `novaic-cortex/tests/test_resolve_for_llm.py`.
- Updated:
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`

## Verification

- `rg "resolve_for_llm"` over active code/test packages returns no results.
- Focused verification:
  - Cortex projection tests: `18 passed`.
  - Runtime projection/multimodal guard tests: `10 passed`.
  - Factory chat/log tests: `16 passed`.

## Residual Risk

Full-suite and deployment verification remain outside this test-residue cleanup parent. Google/Gemini multimodal conversion remains an active provider gap to handle in the regression/follow-up path.

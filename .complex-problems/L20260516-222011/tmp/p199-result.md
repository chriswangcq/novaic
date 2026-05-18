# Projection production stale branch cleanup parent result

## Summary

Completed production stale branch cleanup. The stale `resolve_for_llm` helper/export was removed, caller evidence was recorded, and retained production projection branches were either deleted, narrowed, or justified with tests.

## Child Results

- `R191` / `P207`: Proved `resolve_for_llm` has no live in-repo production callers and identified deletion targets.
- `R192` / `P208`: Removed `resolve_for_llm`, its root package export, stale helper documentation, and unused imports.
- `R196` / `P209`: Audited retained branches:
  - removed nested `result` unwrapping,
  - retained display image branch only for explicit display perception,
  - bounded unknown dict fallback.

## Production Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/novaic_cortex/__init__.py`

## Test Changes

- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`

## Verification

- Production `rg` confirms no remaining `resolve_for_llm` references in Cortex/runtime/factory/common production packages.
- Final focused Cortex projection run:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py
```

Result: `18 passed in 0.06s`.

## Remaining Work Outside This Problem

- `novaic-cortex/tests/test_resolve_for_llm.py` remains stale test residue for P200.
- Google/Gemini multimodal provider conversion remains an active provider gap for later tickets.
- Runtime projection routing should be included in the final regression sweep.

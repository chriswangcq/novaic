# Cortex operational store generation validation result

## Summary

Patched Cortex operational store generation write boundaries so projection and active-stack writes use explicit non-negative generation validation rather than raw `int(generation)`.

## Done

- Updated `novaic-cortex/novaic_cortex/operational_store.py`:
  - `upsert_scope_projection` now validates generation via `_require_non_negative_generation(..., "scope projection upsert")`.
  - `set_active_stack` now validates generation via `_require_non_negative_generation(..., "active stack projection")`.
- Added `test_operational_store_rejects_invalid_generation_boundaries` to cover bool and negative generation rejection for event append, projection upsert, and active stack persistence.

## Verification

- `python3 -m py_compile novaic_cortex/operational_store.py novaic_cortex/active_stack_projection.py novaic_cortex/api.py` passed.
- `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_operational_store.py tests/test_active_stack_projection.py tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_write_authority.py tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_pr74_scope_summary_contract.py` passed: 104 tests.
- Cross-repo generation coercion guard returned no matches for the target runtime/Cortex directories.

## Known Gaps

- Remaining active/finalize/archive textual hits still need a guard-matrix classification in the sibling P388 problem.

## Artifacts

- Patched files: `novaic-cortex/novaic_cortex/operational_store.py`, `novaic-cortex/tests/test_operational_store.py`.

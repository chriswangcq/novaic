# Runtime lifecycle method removal result

## Summary

Removed the direct structural scope lifecycle helpers from the `Cortex` runtime façade and added guard coverage proving they are no longer exposed.

## Done

- Removed `Cortex.scope_create` from `novaic_cortex/runtime.py`.
- Removed `Cortex.scope_end` from `novaic_cortex/runtime.py`.
- Updated the runtime module docstring so it no longer advertises internal scope lifecycle management.
- Extended the legacy lifecycle removal guard test to assert `Cortex` has no `scope_create` or `scope_end` attributes.

## Verification

- Static scan:
  - `rg -n "async def scope_(create|end)" novaic_cortex/runtime.py`
  - Result: no matches.
- Focused guard test:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_legacy_skill_lifecycle_removed.py -q`
  - Result: `3 passed in 0.27s`

## Known Gaps

- Existing legacy tests still call `cortex.scope_create(...)` or `cortex.scope_end(...)` and will fail until the sibling P047 test-migration problem is completed.
- Full Cortex suite was intentionally not run as the terminal verification for this child because P047 must migrate affected tests first.

## Artifacts

- Changed: `novaic-cortex/novaic_cortex/runtime.py`
- Changed: `novaic-cortex/tests/test_legacy_skill_lifecycle_removed.py`

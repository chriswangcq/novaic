# Cortex operational store generation validation

## Problem

`novaic-cortex/novaic_cortex/operational_store.py` still uses raw `int(generation)` in projection and active stack store write paths. These live boundaries need explicit non-negative generation validation.

## Success Criteria

- `upsert_scope_projection` validates generation with the explicit non-negative helper.
- `set_active_stack` validates generation with the explicit non-negative helper.
- Focused Cortex operational store tests reject bool and negative generation inputs for the patched boundaries.
- Existing Cortex context-event tests still pass.
- This belongs under P385 because it closes the Cortex half of the residual live generation coercion list.

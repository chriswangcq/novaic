# Patch Cortex operational store generation validation

## Problem Definition

Cortex operational store still uses raw `int(generation)` in two write paths: scope projection upsert and active stack persistence. These are storage authority boundaries and should reject malformed generation values explicitly.

## Proposed Solution

Use the existing `_require_non_negative_generation` helper in `upsert_scope_projection` and `set_active_stack`, then add focused operational store tests for bool and negative generation rejection.

## Acceptance Criteria

- No raw `int(generation)` remains in `novaic-cortex/novaic_cortex/operational_store.py`.
- Focused operational store tests reject bool and negative generation for the patched paths.
- Existing Cortex context-event/projection tests pass.

## Verification Plan

Run Python compile checks for `novaic_cortex/operational_store.py`, focused operational store tests, active stack projection tests, and context event regression tests.

## Risks

- Cortex may legitimately use generation `0` for initial records, so validation must remain non-negative rather than positive.

## Assumptions

- Bool generations should be rejected even though `bool` is an `int` subclass in Python.

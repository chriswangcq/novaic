# Check: Finalize Diagnostics Aggregate Verification

## Summary

Success. P369 is solved by R361. Aggregate finalize/archive verification passed and one remaining bool-generation coercion gap at the repository boundary was fixed and covered.

## Evidence

- R361 records the repo-level bool generation fix.
- Runtime focused finalize/recovery/compensation suite passed: 57 passed.
- Cortex archive/context suite passed: 55 passed.
- Residue review covered `remaining_stack`, `finalize_reason`, `ended_at`, time/id defaults, and generation lookup around finalize paths.

## Criteria Map

- Run focused session finalize, Cortex archive, recovery/compensation, and wake-finalize tests: satisfied.
- Run residue searches for `remaining_stack`, `finalize_reason`, `ended_at`, generation defaults, and active lookup: satisfied.
- Record/fix remaining gaps before closing P338: satisfied; bool generation coercion at `SessionRepository.session_ended(...)` was fixed directly.

## Execution Map

Verification found one small boundary gap, which was fixed in-place because it was bounded and directly within P369 scope. Tests were rerun after the fix.

## Stress Test

The one-go check was intentionally skeptical: it did not stop at handler-level validation and caught that repository direct callers could still coerce `True` to `1`. That edge is now covered.

## Residual Risk

None for P369.

## Result IDs

- R361

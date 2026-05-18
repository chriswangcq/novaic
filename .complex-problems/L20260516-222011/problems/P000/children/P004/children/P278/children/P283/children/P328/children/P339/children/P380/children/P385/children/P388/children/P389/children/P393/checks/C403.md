# P393 round and stack-depth default classification check

## Summary

Success. Round number and stack-depth defaults in wake finalize/recovery are now explicit and tested.

## Evidence

- Wake finalize and recovery archive paths use `_non_negative_int` for `round_num` and `stack_depth_at_finalize`.
- Focused tests reject bool values and preserve valid payload shape.
- Focused runtime recovery/finalize tests passed: 30 tests.

## Criteria Map

- Wake finalize raw stack-depth parsing removed: satisfied.
- Recovery raw stack-depth/round parsing removed: satisfied.
- Focused tests pass: satisfied.
- Remaining helper calls classified as safe explicit parsing: satisfied.

## Execution Map

- R380 records patches, tests, compile check, and targeted guard outcome.

## Stress Test

- Tests cover bool values for both `round_num` and `stack_depth_at_finalize`, preventing Python bool-to-int coercion.

## Residual Risk

- None for scoped round/stack-depth defaults.

## Result IDs

- R380

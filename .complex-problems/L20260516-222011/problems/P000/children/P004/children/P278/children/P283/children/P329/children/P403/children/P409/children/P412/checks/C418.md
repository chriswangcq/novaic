# React contract residue classification check

## Summary

`P412` is successful. The two React contract files were guarded, `session_generation` is explicit/positive, and remaining numeric defaults are loop-control counters with focused contract tests passing.

## Evidence

- `R392` records the targeted guard artifact and classifications.
- `tests/test_runtime_explicit_contracts.py` passed: `16 passed in 0.13s`.
- Guard output shows `session_generation` goes through shared positive-generation helpers.

## Criteria Map

- Inspect React contract guard hits: satisfied.
- Confirm `session_generation` is explicit and validated: satisfied by helper imports/usages and tests.
- Classify round/retry/stack-depth defaults: satisfied by `R392`.
- Run focused React contract tests: satisfied.

## Execution Map

- `T399` executed as a two-file one-go classification.
- Initial test run from the subdirectory passed, but guard paths were wrong; execution corrected that by rerunning the guard from the repo root before recording `R392`.

## Stress Test

- The check treats the path mistake as part of the review: the final result relies on the corrected guard, not the earlier empty output.

## Residual Risk

- None for P412.

## Result IDs

- `R392`

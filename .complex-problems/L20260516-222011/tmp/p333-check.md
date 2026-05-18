# Check: Attach stale and missing generation regression coverage audit

## Summary

Success. The aggregate one-go verification earned closure: it covers all three attach layers, includes both positive and negative cases, and source-guards the removed repository fallback helpers.

## Evidence

- R318 lists a layer-by-layer coverage matrix.
- Focused attach generation suite passed: `31 passed`.
- Source guard found no `active_generation(...)`, `_active_session_generation_after_transaction`, or explicit `expected_session_generation = None` residue.
- P330/P331/P332 provided the underlying fixes/tests used by the aggregate coverage.

## Criteria Map

- Coverage matrix lists repository, outbox, and runtime tests: satisfied by R318.
- Focused attach generation suite passes: satisfied by `31 passed`.
- Source guard confirms old repository fallback helpers are gone: satisfied.
- Any uncovered stale/missing generation path fixed or followed up: satisfied; no uncovered path remained after P330-P332.

## Execution Map

- T323 executed aggregate verification after child fixes.
- No additional code change was required in this aggregate step.

## Stress Test

- Repository race/stale scope: covered by P330 regression.
- Missing generation at outbox: covered by P331 regression.
- Missing/stale scope/generation at runtime: covered by P332 regression.
- Happy path still passes across repository/outbox/runtime focused tests.

## Residual Risk

- None for aggregate attach generation coverage.

## Result IDs

- R318

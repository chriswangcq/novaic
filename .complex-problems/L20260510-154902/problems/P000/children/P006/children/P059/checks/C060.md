# P059 success check

## Result IDs

- R057

## Criteria Map

- Missing/empty event logs raise explicit reset-required behavior: satisfied.
- No DFS fallback in reset-required cases: satisfied by prepare/status tests on legacy-only roots.
- Tests cover read model, prepare endpoint, and status include-usage endpoint: satisfied.
- Full Cortex suite passes: satisfied.

## Execution Map

- Added reset-required exception.
- Translated exception to explicit HTTP 409 API behavior.
- Added focused no-compat tests.

## Evidence

- Focused tests: `7 passed`.
- Full Cortex suite: `455 passed`.

## Stress Test

- Tests create legacy-only materialized roots through direct workspace projection helpers and then prove active API usage refuses them instead of producing DFS-derived context.

## Residual Risk

- Runtime/UI must handle reset-required responses explicitly. That is expected full-cut behavior, not a compatibility gap.

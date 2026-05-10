# Runtime lifecycle helper test migration check

## Summary

Success. P047 is solved: all tests have been migrated off removed runtime lifecycle helpers, and the focused affected test bundle passes.

## Evidence

- Parent-level static scan over `tests/` found no `.scope_create(` or `.scope_end(` calls.
- Parent-level focused test bundle passed: `26 passed in 0.35s`.
- Child checks P049, P050, and P051 are all successful.

## Criteria Map

- No test uses `cortex.scope_create(...)` or `cortex.scope_end(...)`: satisfied.
- Lifecycle archival tests use API/context paths or projection setup: satisfied.
- Obsolete hook/metric runtime lifecycle expectations removed or replaced: satisfied.
- Focused migrated test files pass: satisfied.

## Execution Map

- R039 handled archive/summary tests.
- R042 handled hooks/metrics tests.
- R043 handled miscellaneous tests.
- R044 summarized parent migration and parent-level verification.

## Stress Test

- The check uses the broad `tests/` scan rather than only enumerating known files, so newly discovered helper residue would fail the check.

## Residual Risk

- Full-suite verification and repo-wide runtime bypass scan remain tracked by P048.

## Result IDs

- R044

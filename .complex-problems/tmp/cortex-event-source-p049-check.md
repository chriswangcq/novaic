# Archive and summary test migration check

## Summary

Success. P049 is solved: the two archive/summary test files no longer call the removed runtime lifecycle helper and their focused tests pass through the API lifecycle path.

## Evidence

- Static scan over the affected files found no `.scope_end(` calls.
- Focused test run passed: `11 passed in 0.27s`.
- The structural empty-summary assertion is still present and now uses `scope_end(ScopeEndRequest(...))`.

## Criteria Map

- `tests/test_archive_invariants.py` no longer calls `cortex.scope_end(...)`: satisfied.
- `tests/test_pr74_scope_summary_contract.py` no longer calls `cortex.scope_end(...)`: satisfied.
- Structural scope ending uses API `scope_end`: satisfied.
- Focused archive/summary tests pass: satisfied.

## Execution Map

- R039 changed the two test files.
- R039 verified static scan and focused tests.

## Stress Test

- The scan targeted the exact removed runtime helper pattern in both files, not just runtime method definitions.
- Tests still exercise archive metadata and summary persistence after API structural close.

## Residual Risk

- Other test families remain in P050/P051 and are outside this child’s scope.

## Result IDs

- R039

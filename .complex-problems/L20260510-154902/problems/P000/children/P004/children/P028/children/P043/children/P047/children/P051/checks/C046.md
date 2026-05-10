# Miscellaneous runtime lifecycle test migration check

## Summary

Success. P051 is solved: the miscellaneous test files no longer use removed runtime lifecycle helpers, and their focused tests pass.

## Evidence

- Static scan over `test_engine_wiring.py`, `test_compaction_meta.py`, and `test_cortex_chaos.py` found no `.scope_create(` or `.scope_end(` calls.
- Focused test run passed: `7 passed in 0.28s`.

## Criteria Map

- The three miscellaneous test files have no runtime lifecycle helper calls: satisfied.
- Focused miscellaneous tests pass: satisfied.
- Original engine config, archive meta, and chaos churn assertions remain meaningful: satisfied by focused test pass and retained assertions.

## Execution Map

- R043 migrated engine and compaction tests to API `scope_end`.
- R043 verified `test_cortex_chaos.py` no longer had runtime helper residue after earlier metric cleanup.

## Stress Test

- The static scan covered both create and end helper patterns across all three target files.

## Residual Risk

- Repo-wide verification remains tracked by P048.

## Result IDs

- R043

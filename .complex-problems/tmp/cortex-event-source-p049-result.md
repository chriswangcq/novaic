# Archive and summary test migration result

## Summary

Migrated archive/summary lifecycle tests away from the removed runtime `cortex.scope_end(...)` helper and onto the event-wired API `scope_end` handler.

## Done

- Added API registry/lock setup helpers to `tests/test_archive_invariants.py`.
- Replaced runtime `cortex.scope_end(...)` usages in archive invariant tests with `scope_end(ScopeEndRequest(...))`.
- Updated `tests/test_pr74_scope_summary_contract.py` so the remaining runtime-named structural summary test uses API `scope_end`.
- Kept the structural close invariant: API structural close writes an empty `summary.md`.

## Verification

- Static scan:
  - `rg -n "\\.scope_end\\(" tests/test_archive_invariants.py tests/test_pr74_scope_summary_contract.py`
  - Result: no matches.
- Focused tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_archive_invariants.py tests/test_pr74_scope_summary_contract.py -q`
  - Result: `11 passed in 0.27s`

## Known Gaps

- Other test families still call removed runtime lifecycle helpers and are tracked by sibling P050/P051.

## Artifacts

- Changed: `novaic-cortex/tests/test_archive_invariants.py`
- Changed: `novaic-cortex/tests/test_pr74_scope_summary_contract.py`

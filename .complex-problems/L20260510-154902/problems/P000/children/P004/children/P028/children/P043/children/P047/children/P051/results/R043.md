# Miscellaneous runtime lifecycle test migration result

## Summary

Migrated the remaining miscellaneous runtime lifecycle test call sites to API `scope_end` and confirmed `test_cortex_chaos.py` has no runtime lifecycle helper residue.

## Done

- Replaced runtime `cortex.scope_end(...)` calls in `tests/test_engine_wiring.py` with API `scope_end(ScopeEndRequest(...))`.
- Replaced runtime `cortex.scope_end(...)` calls in `tests/test_compaction_meta.py` with API `scope_end(ScopeEndRequest(...))`.
- Added local test registry/lock setup in those files for API handler execution.
- Confirmed the three miscellaneous files have no `.scope_create(` or `.scope_end(` runtime helper calls.

## Verification

- Static scan:
  - `rg -n "\\.scope_create\\(|\\.scope_end\\(" tests/test_engine_wiring.py tests/test_compaction_meta.py tests/test_cortex_chaos.py`
  - Result: no matches.
- Focused tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_engine_wiring.py tests/test_compaction_meta.py tests/test_cortex_chaos.py -q`
  - Result: `7 passed in 0.28s`

## Known Gaps

- Repo-wide static/full verification remains tracked by P048.

## Artifacts

- Changed: `novaic-cortex/tests/test_engine_wiring.py`
- Changed: `novaic-cortex/tests/test_compaction_meta.py`

# Workspace hook test migration result

## Summary

Migrated hook-emission tests from removed runtime lifecycle helpers to Workspace lifecycle projection methods.

## Done

- Rewrote `tests/test_hooks_metrics.py` to use `make_workspace_with_store` plus `create_scope_projection` / `archive_root_scope_projection`.
- Rewrote hook-focused cases in `tests/test_hooks_limits.py` to exercise Workspace hook emission directly.
- Removed obsolete runtime scope lifecycle metric assertions from these hook tests.
- Kept hook callback success/failure/isolation assertions.

## Verification

- Static scan:
  - `rg -n "\\.scope_create\\(|\\.scope_end\\(" tests/test_hooks_metrics.py tests/test_hooks_limits.py`
  - Result: no matches.
- Focused hook tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_hooks_metrics.py tests/test_hooks_limits.py -q`
  - Result: `7 passed in 0.08s`

## Known Gaps

- Dead runtime scope lifecycle metric fields remain for P053.

## Artifacts

- Changed: `novaic-cortex/tests/test_hooks_metrics.py`
- Changed: `novaic-cortex/tests/test_hooks_limits.py`

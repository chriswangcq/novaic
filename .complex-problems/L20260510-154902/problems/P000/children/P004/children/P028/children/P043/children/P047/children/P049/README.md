# Migrate archive and summary lifecycle tests

## Problem

Archive/summary tests currently use `cortex.scope_end(...)` to close scopes. That removed runtime helper must be replaced with event-wired API lifecycle handlers without changing the archive invariant being tested.

## Success Criteria

- `tests/test_archive_invariants.py` no longer calls `cortex.scope_end(...)`.
- `tests/test_pr74_scope_summary_contract.py` no longer calls `cortex.scope_end(...)`.
- Tests that validate structural scope ending use `novaic_cortex.api.scope_end` with `ScopeEndRequest`.
- Focused archive/summary tests pass.

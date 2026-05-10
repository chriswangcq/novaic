# Result: Old Lazy-RO Branch Removed From Current Path

## Summary

Cut over tests and residue for the shell path. The old command-gated RO materialization behavior is no longer encoded as a desired behavior, and focused sandbox tests pass against the LogicalFS boundary.

## Done

- Replaced `test_shell_skips_ro_materialization_when_command_only_needs_rw` with `test_shell_materializes_full_logical_view_without_command_gating`.
- Added explicit provider capability test for `local-mirror`, `true_stable_path_mount=False`, and outer-command adapter behavior.
- Added RW layout environment test for `RW_PUBLIC`, `RW_SELF`, `RW_TMP`, `RW_ARTIFACTS`, and `RW_SCRATCH`.
- Renamed old lazy-RO test names and agent IDs.
- Removed stale “Disposable sandbox” wording from a test docstring.
- Confirmed old command-gating symbols are absent from `novaic_cortex` and tests.

## Verification

- `pytest -q tests/test_incremental_sync.py tests/test_sandbox_sync.py` passed: 14 passed.
- Residue audit passed with no matches for:
  - `_command_needs_ro`
  - `_materialize_workspace`
  - `_persist_rw_changes`
  - `_rewrite_stable_cortex_paths`
  - `_RO_ENV_RE`
  - `_STABLE_RO_PATH_RE`
  - lazy-RO / command-needs-RO phrases

## Known Gaps

- References to `novaic-cortex-sandbox-*` intentionally remain only for rejecting leaked old ephemeral paths and tests that prove sanitized output. P004 must decide whether schema docs should keep or reword that user guidance.

## Artifacts

- `novaic-cortex/tests/test_sandbox_sync.py`
- `novaic-cortex/tests/test_incremental_sync.py`
- `novaic-cortex/novaic_cortex/sandbox.py`

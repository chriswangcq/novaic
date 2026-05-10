# Common sandbox module implementation result

## Summary

Created `common.sandbox` base infrastructure modules for generic process execution, mount namespace command construction/capability detection, and filesystem helpers.

## Done

- Added `novaic-common/common/sandbox/process.py`
  - `ProcessSpec`
  - `ProcessRunResult`
  - `AsyncProcessRunner`
- Added `novaic-common/common/sandbox/mount_namespace.py`
  - `mount_namespace_available`
  - `build_bind_mount_command`
- Added `novaic-common/common/sandbox/filesystem.py`
  - `file_stats`
  - `changed_relative_paths`
  - `safe_path_component`
  - `resolve_cwd_under_root`
  - `is_keep_placeholder`
  - `sanitize_paths`
- Added package exports in `common/sandbox/__init__.py`.
- Added `novaic-common/tests/test_sandbox_infra.py`.

## Evidence

- Targeted common tests: `6 passed`.
- Common sandbox modules compile with `PYTHONPATH=. python -m py_compile`.

## Notes

The common mount namespace tests intentionally verify command construction, not actual root/unshare execution. The real mount integration remains a Cortex-level responsibility.

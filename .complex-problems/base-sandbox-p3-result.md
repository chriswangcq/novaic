# Cortex migration result

## Summary

Cortex now consumes the common sandbox infrastructure modules. The local Cortex process runner was deleted, and generic mount/filesystem helpers were replaced with imports from `common.sandbox`.

## Done

- Updated `novaic_cortex/sandbox.py` to use `common.sandbox.process.AsyncProcessRunner` and `ProcessSpec`.
- Updated `novaic_cortex/logical_fs.py` to use:
  - `common.sandbox.filesystem.file_stats`
  - `changed_relative_paths`
  - `safe_path_component`
  - `resolve_cwd_under_root`
  - `is_keep_placeholder`
  - `sanitize_paths`
  - `common.sandbox.mount_namespace.mount_namespace_available`
  - `build_bind_mount_command`
- Deleted `novaic_cortex/sandbox_exec.py`.
- Updated the mount-unavailable test to monkeypatch the canonical LogicalFS module.

## Evidence

- Cortex targeted tests passed: `7 passed, 13 skipped`.
- Full Cortex tests passed: `342 passed, 41 skipped`.
- Common sandbox targeted tests passed: `6 passed`.
- Residue scan shows no `novaic_cortex.sandbox_exec`, `class SandboxExec`, local `ProcessSpec`, or local generic helper definitions.

## Notes

Cortex still owns the product-specific `MountNamespaceLogicalFS`, `/cortex` stable paths, `/ro`/`/rw` layout, Workspace materialization, and shell capability commands.

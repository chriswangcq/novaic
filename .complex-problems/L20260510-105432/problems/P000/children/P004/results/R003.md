# Verification and residue result

## Summary

Verified the common base extraction across `novaic-common` and `novaic-cortex`. The common sandbox modules are active in Cortex and full tests pass in both repos.

## Done

- Ran full `novaic-common` tests.
- Ran full `novaic-cortex` tests.
- Ran compile checks over common sandbox modules and migrated Cortex modules.
- Ran residue scan for old local process runner, old local generic filesystem helpers, old command rewrite/lazy RO helpers, and old `novaic_cortex.sandbox_exec` imports.

## Evidence

- `novaic-common`: `145 passed`.
- `novaic-cortex`: `342 passed, 41 skipped`.
- Residue scan shows:
  - `ProcessSpec` only in `common.sandbox.process`.
  - `AsyncProcessRunner` imported by Cortex from `common.sandbox.process`.
  - `build_bind_mount_command` imported by Cortex from `common.sandbox.mount_namespace`.
  - No `novaic_cortex.sandbox_exec` imports.
  - No `class SandboxExec`.
  - No local `_rw_file_stats`, `_safe_path_component`, `_resolve_cwd_under_rw`, `_is_keep_placeholder`, old command rewrite, or lazy RO helpers.

## Residual Risk

One Cortex-specific wrapper remains: `_sanitize_cortex_paths`, which maps actual paths to Cortex stable `/cortex` paths using the common `sanitize_paths` helper. This is intentionally not a generic duplicate because it embeds Cortex path constants.

The working tree also contains unrelated prior dirty changes in `novaic-common` and `novaic-cortex`; they were not reverted or modified outside this task.

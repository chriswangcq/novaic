# Generic sandbox primitive audit result

## Summary

The stable business-agnostic pieces are generic process execution, OS mount namespace command construction/capability detection, and low-level filesystem helpers. Cortex-specific pieces must stay in Cortex.

## Common Infrastructure Candidates

- `ProcessSpec`, `ProcessRunResult`, and the async subprocess runner: stable input/output, no Cortex semantics.
- `mount_namespace_available`: OS capability detection only.
- Bind-mount command construction for `unshare --mount` with caller-provided source root, mount point, stable cwd, and command: generic OS substrate.
- Filesystem snapshot/diff helpers: relative file stat maps and changed relative paths.
- Safe path component normalization: generic string hygiene for path segments.
- Root-relative cwd resolution: generic sandbox safety primitive.
- Output path sanitization from actual paths to stable paths: generic replacement utility.

## Cortex-Specific Non-Candidates

- `MountNamespaceLogicalFS`: depends on Workspace `/ro`/`/rw`, token env, shell capability scripts, and agent/subagent RW layout.
- `LogicalFSView` as currently shaped: includes Cortex stable paths, capability bin, env, and RW tracking.
- `LogicalFSCapabilities`: still carries Cortex transition fields like `outer_command_path_adapter`.
- `STABLE_CORTEX_*`: product path contract.
- `_logical_rw_path`: maps changed relative files into Cortex `/rw/...`.
- Shell capabilities (`agentctl`, `cortex`, `devicectl`): product/agent interface.
- Ephemeral Cortex sandbox path rejection: Cortex UX/policy.

## Target APIs

- `common.sandbox.process`
  - `ProcessSpec`
  - `ProcessRunResult`
  - `AsyncProcessRunner`
- `common.sandbox.mount_namespace`
  - `mount_namespace_available()`
  - `build_bind_mount_command(...)`
- `common.sandbox.filesystem`
  - `file_stats(root)`
  - `changed_relative_paths(before, after)`
  - `safe_path_component(value, default)`
  - `resolve_cwd_under_root(root, cwd)`
  - `is_keep_placeholder(path, data)`
  - `sanitize_paths(text, replacements)`

## Evidence

Inspected `novaic_cortex/sandbox_exec.py`, `novaic_cortex/logical_fs.py`, `novaic_cortex/sandbox.py`, and sandbox tests. The extracted candidate APIs have no dependency on Workspace, Blob, scopes, agents, or Cortex tool contracts.

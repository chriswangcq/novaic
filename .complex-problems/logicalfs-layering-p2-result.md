# Module extraction result

## Summary

Extracted the monolithic shell implementation into explicit modules without changing the public `Sandbox` facade.

## Done

- Added `novaic_cortex/shell_capabilities.py` for injected shell commands (`agentctl`, `cortex`, `devicectl`) and explicit capability env filtering.
- Added `novaic_cortex/logical_fs.py` for stable `/cortex/{ro,rw}` constants, LogicalFS view/capabilities, mount namespace provider, materialization, flush, RW layout, and path sanitization.
- Added `novaic_cortex/sandbox_exec.py` for generic process execution dataclasses and runner.
- Reduced `novaic_cortex/sandbox.py` to policy rejection, `ShellExecutionOrchestrator`, and public `Sandbox` facade.
- Kept selected compatibility imports/re-exports from `sandbox.py` so current tests that import `_logical_rw_changes` or `_mount_namespace_available` still point to canonical implementations.

## Evidence

- `novaic_cortex/sandbox.py` is now 181 lines.
- `novaic_cortex/logical_fs.py` owns `class MountNamespaceLogicalFS`.
- `novaic_cortex/sandbox_exec.py` owns `class SandboxExec`.
- `novaic_cortex/shell_capabilities.py` owns `_CAPABILITY_SCRIPT`.
- Import check with `PYTHONPATH=../novaic-common:.` succeeded for `Sandbox`, `MountNamespaceLogicalFS`, `SandboxExec`, and `_capability_env`.
- Targeted local pytest command over sandbox/capability tests completed with `1 passed, 32 skipped`; local skips are expected because this host lacks the root/unshare/mount substrate.

## Notes

The extraction is mechanical: no local fallback or command rewrite fallback was reintroduced.

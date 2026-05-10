# Result: Active Path And Host Capability Audit

## Summary

Audited the current Cortex shell execution path and host substrate. The active path is still `Cortex.tool_shell -> Sandbox.exec -> temp workspace projection -> process -> RW diff/persist`, with command-string RO gating still present before implementation.

## Done

- Active runtime entry:
  - `novaic-cortex/novaic_cortex/runtime.py` constructs `Sandbox(...)`.
  - `Cortex.tool_shell(...)` calls `self.sandbox.exec(command, timeout, extra_env=env)`.
  - `novaic-cortex/novaic_cortex/api.py` shell endpoint calls `cortex.tool_shell(...)`.
- Active old sandbox logic:
  - `novaic-cortex/novaic_cortex/sandbox.py` defines `_command_needs_ro`.
  - `Sandbox.exec` calls `_command_needs_ro(command)`.
  - `Sandbox._materialize_workspace` owns RO/RW store materialization.
  - `Sandbox._persist_rw_changes` owns RW persistence.
  - `Sandbox.exec` rewrites stable `/cortex` paths in the outer command string.
- Tests currently encode old behavior:
  - `tests/test_sandbox_sync.py` has lazy-RO tests.
  - Stable path tests assert output sanitization and outer command reuse.
- Host capability check:
  - uid is `501`.
  - `/cortex` does not exist.
  - `fuse`, `fusepy`, `llfuse`, and `pyfuse3` are not importable.
  - `proot` and `unshare` are not available.
  - `/sbin/mount` exists, but current process does not have root/mount setup for a private `/cortex`.

## Verification

- Used `rg` to locate active code and old symbols.
- Used Python import checks for FUSE-related modules and shell capability checks for mount namespace substitutes.

## Known Gaps

- True hidden-literal `/cortex` semantics cannot be honestly claimed on this host with the currently available substrate. The implementation must model this as a provider capability limitation while still removing old command-string RO gating and moving filesystem ownership to LogicalFS.

## Artifacts

- Code pointers:
  - `novaic-cortex/novaic_cortex/runtime.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-cortex/tests/test_sandbox_sync.py`

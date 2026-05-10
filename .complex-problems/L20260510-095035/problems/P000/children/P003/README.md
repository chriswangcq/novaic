# Cut Over Active Shell Path And Remove Old Branches

## Problem

Route the active shell execution path through the new boundary and physically remove or quarantine the old command-gated temp-projection logic. This closes the common failure mode where new code exists but old logic still runs.

## Success Criteria

- `Sandbox.exec` routes through ShellExecutionOrchestrator.
- Command-string RO gating is removed from active code.
- Old `_materialize_workspace` and `_persist_rw_changes` authority is removed from `Sandbox`.
- Tests no longer encode lazy-RO behavior as desired.
- `rg` audit proves old command-gating symbols are absent or unreachable.

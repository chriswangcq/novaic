# Wire shell execution path through LogicalFS view then sandboxd

## Problem

Shell execution must become a clear sequence: Cortex state adapter creates snapshot, LogicalFS creates a view, sandboxd executes against that view, LogicalFS observes patch, Cortex applies patch.

## Success Criteria

- `Sandbox.exec` or equivalent orchestrator follows the explicit sequence without hidden Cortex reads inside LogicalFS.
- Sandboxd still receives a SDK `SandboxExecSpec` and core substrate stays behind sandboxd.
- Tests prove the request sent to sandboxd contains a LogicalFS view handle/mount input from the LogicalFS package.
- Local fallback remains absent.

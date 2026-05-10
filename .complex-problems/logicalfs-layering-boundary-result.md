# LogicalFS layering cleanup result

## Summary

Completed the system layering audit and refactor. The final model is:

```text
Call flow: Cortex runtime/API -> Sandbox facade -> LogicalFS + process runner
Storage dependency: LogicalFS -> Workspace logical port -> CortexStore -> BlobCortexStore
Shell UX: process sees stable /cortex/{ro,rw}
```

Blob remains the byte-object substrate. LogicalFS is the filesystem view over Workspace/store/blob and the layer closest to shell execution.

## Done

- P001 audited the active path and clarified call-flow versus dependency-flow terminology.
- P002 extracted the monolithic `sandbox.py` implementation into:
  - `novaic_cortex/shell_capabilities.py`
  - `novaic_cortex/logical_fs.py`
  - `novaic_cortex/sandbox_exec.py`
  - thin `novaic_cortex/sandbox.py` facade/orchestrator
- P003 added `Workspace.read_tree_bytes` so LogicalFS no longer touches `Workspace._store` or `_key`.
- P004 verified the refactor with compile checks, targeted tests, full tests, and residue scans.

## Evidence

- `novaic_cortex/sandbox.py` is now 181 lines and only owns policy rejection, orchestration, and public `Sandbox`.
- `novaic_cortex/logical_fs.py` owns `MountNamespaceLogicalFS`.
- `novaic_cortex/sandbox_exec.py` owns `SandboxExec`.
- `novaic_cortex/shell_capabilities.py` owns shell capability scripts.
- Full `novaic-cortex` test suite passed: `342 passed, 41 skipped`.
- Residue scan found no active old command rewrite/lazy RO/local fallback implementation.

## Residual Risk

Local mount namespace execution remains skipped on this host because root/unshare/mount are production-substrate requirements. No deployment smoke was run in this architecture cleanup pass.

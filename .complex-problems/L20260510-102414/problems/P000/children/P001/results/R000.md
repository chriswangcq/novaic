# Layering audit result

## Summary

The current runtime path is conceptually close but physically muddled. The active call path is:

```text
Cortex API/runtime
  -> Cortex.tool_shell / Sandbox facade
  -> ShellExecutionOrchestrator
  -> MountNamespaceLogicalFS acquire/process/release
  -> Workspace logical paths
  -> CortexStore
  -> BlobCortexStore in production
```

The storage dependency path is:

```text
Blob/Object storage bytes
  -> CortexStore object API
  -> Workspace path/scope semantics
  -> LogicalFS stable /cortex/{ro,rw} filesystem view
  -> Sandbox process execution
  -> Cortex shell tool surface
```

So the user's intuition is right about Cortex being the top policy layer and Sandbox being below Cortex. The only wording trap is Blob versus LogicalFS: Blob is lower-level byte storage; LogicalFS is the filesystem view built over Workspace/store/blob. If "最后" means "closest to shell/user experience", LogicalFS is last. If "最后" means "lowest primitive dependency", Blob is last.

## Done

- Audited `novaic_cortex/api.py` `/v1/shell` and `/v1/internal/shell`, which construct `Cortex` and call `tool_shell`.
- Audited `novaic_cortex/runtime.py`, where `Cortex` owns `Workspace` and constructs `Sandbox(self.workspace, ...)`.
- Audited `novaic_cortex/sandbox.py`, where the file already has conceptual comments but physically mixes capability CLI, LogicalFS, process execution, and facade/orchestrator.
- Audited `novaic_cortex/workspace.py`, which owns path/scope semantics and currently exposes `read_bytes`/`write_bytes` but not a public recursive byte listing port.
- Audited `novaic_cortex/store.py` and `novaic_cortex/blob_store.py`; BlobCortexStore is clearly the production object-storage substrate under CortexStore.

## Evidence

- `novaic_cortex/api.py:266` and `novaic_cortex/api.py:1871` call shell through `Cortex.tool_shell`.
- `novaic_cortex/runtime.py:66` and `novaic_cortex/runtime.py:77` construct `Sandbox` with `Workspace`.
- `novaic_cortex/sandbox.py:1065` defines `MountNamespaceLogicalFS`.
- `novaic_cortex/sandbox.py:1320` defines `SandboxExec`.
- `novaic_cortex/sandbox.py:1355` defines `ShellExecutionOrchestrator`.
- `novaic_cortex/sandbox.py:1445` defines the public `Sandbox` facade.
- `novaic_cortex/workspace.py:176`/`:210` expose byte read/write, while `sandbox.py` still reaches into `Workspace._store` and `_key`.
- `novaic_cortex/store.py:19` defines `CortexStore` as pure object storage.
- `novaic_cortex/blob_store.py:18` implements production `BlobCortexStore`.

## Architectural Decision

Canonical module direction should be:

```text
runtime/api -> sandbox facade -> logical_fs + process_exec
logical_fs -> workspace storage port -> workspace -> CortexStore -> BlobCortexStore
shell_capabilities -> CLI scripts exposed inside LogicalFS bin
```

LogicalFS should not be below Blob. LogicalFS provides directory/path/mount semantics over the lower object-store/blob substrate.

## Follow-up Inputs

- Extract shell capability CLI into its own module.
- Extract LogicalFS into its own module.
- Extract process execution into its own module.
- Add a public Workspace storage-port method so LogicalFS does not reach into `_store` and `_key` as the normal dependency.

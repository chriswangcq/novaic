# Cortex Boundary Call Path Map Result

## Summary

Cortex boundary mapping is complete for `novaic-cortex`. The current shell path is Cortex semantic adapter -> generic LogicalFS substrate -> sandboxd executor, with no alternate local shell execution fallback. Blob usage in Cortex appears as payload/artifact storage and capability CLI upload/download, not as the live RO/RW filesystem authority. One potentially stale naming/API surface, `Workspace.materialize()`, is flagged for the later residue inventory because it writes external bytes to `/rw/scratch`.

## Done

- Generated Cortex boundary scan: `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-scan.txt`.
- Generated scan counts: `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-counts.md`.
- Generated high-signal source slices: `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-slices.txt`.
- Inspected:
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-cortex/novaic_cortex/logical_fs.py`
  - `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - `novaic-cortex/novaic_cortex/blob_payload.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`
  - `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`

## Verification

- Cortex boundary scan found 1151 keyword hits across 78 files; this is expected because the scan includes tests and broad terms such as `workspace`.
- Shell execution direction:
  - `Sandbox` composes `MountNamespaceLogicalFS` and `sandbox_sdk` executor.
  - If no sandbox executor is configured, shell execution fails explicitly.
  - Tests assert no local fallback and reject ephemeral `novaic-cortex-sandbox-*` backing paths.
- LogicalFS direction:
  - `MountNamespaceLogicalFS` adapts Cortex `Workspace` semantics to generic `logicalfs.LocalLogicalFSProvider`.
  - It projects bounded `/ro` and `/rw` views into stable `/cortex/ro` and `/cortex/rw` paths.
  - It releases RW changes back to Workspace by observing a LogicalFS patch.
- Blob direction:
  - `blob_payload.py` is a narrow adapter for large Cortex work-trace payloads to `blob://cortex-payload/...`.
  - Capability CLI code uploads device media/file outputs as `tool-output.v1` runtime artifacts instead of printing base64.

## Known Gaps

- `Workspace.materialize()` remains as a Cortex API that writes external bytes into `/rw/scratch`; it is not proven risky here, but it should be classified in P553 because the name overlaps with old direct materialization semantics.
- This child only maps Cortex-side calls. Sandbox/LogicalFS service internals are handled by P560, and artifact/blob classification is handled by P561.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-counts.md`
- `.complex-problems/L20260516-222011/tmp/p559/cortex-boundary-slices.txt`

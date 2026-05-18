# Sandbox LogicalFS Blob Service Call Path Map Result

## Summary

Sandbox/LogicalFS service-side call mapping is complete. `novaic-sandbox-service` is a process execution service with optional bind-mount support; it does not own LogicalFS semantics or blob storage. `novaic-logicalfs` owns generic snapshot materialization/diff mechanics and includes a `BlobObjectStore` adapter below LogicalFS for object storage. This matches the intended direction: Cortex adapts Workspace semantics into LogicalFS, sandboxd executes with a bind-mounted view, and blob remains below LogicalFS or artifact payload storage.

## Done

- Generated scan artifact: `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-boundary-scan.txt`.
- Generated count artifact: `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-counts.md`.
- Generated source slices: `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-slices.txt`.
- Inspected:
  - `novaic-sandbox-service/sandbox_service/main.py`
  - `novaic-sandbox-service/sandbox_service/core/process.py`
  - `novaic-sandbox-service/sandbox_service/core/mount_namespace.py`
  - `novaic-logicalfs/logicalfs/local.py`
  - `novaic-logicalfs/logicalfs/blob_store.py`

## Verification

- Scan found 634 broad keyword hits across 23 files, mostly tests and expected boundary files.
- Sandbox service direction:
  - `/v1/execute` accepts SDK request DTOs, validates cwd/mount specs, and delegates to `AsyncProcessRunner`.
  - `AsyncProcessRunner` runs shell commands with explicit cwd/env/timeout and wraps commands in a bind-mount namespace when a mount plan is provided.
  - `mount_namespace.py` builds the private `unshare --mount` / `mount --bind` command; policy is caller-owned.
- LogicalFS direction:
  - `LocalLogicalFSProvider.materialize()` materializes explicit snapshots into local RO/RW/bin views.
  - `observe_patch()` computes RW upserts/deletes after execution.
  - `sanitize_output()` rewrites backing paths to stable `/cortex` paths.
- Blob direction:
  - `BlobObjectStore` is explicitly documented as an object-store adapter below LogicalFS.
  - Sandbox service itself does not call blob service.

## Known Gaps

- `BlobObjectStore` is a powerful adapter and should be checked in P553/P561 to ensure it is not used as a semantic Workspace API.
- This map does not yet prove every caller uses sandboxd correctly; P553/P555 will scan and verify residues after the full map.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-counts.md`
- `.complex-problems/L20260516-222011/tmp/p560/sandbox-logicalfs-slices.txt`

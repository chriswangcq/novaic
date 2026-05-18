# LogicalFS Sandbox Blob Module Inventory Result

## Summary

Completed a read-only inventory of local modules relevant to Cortex/LogicalFS/sandbox/blob layering. The local checkout contains `novaic-cortex`, `novaic-logicalfs`, `novaic-sandbox-service`, `novaic-sandbox-sdk`, `novaic-blob-service`, `novaic-agent-runtime`, and `novaic-business`. There is no separate `novaic-sandbox-core` root; sandbox core appears under `novaic-sandbox-service/sandbox_service/core`.

## Done

- Generated root inventory: `.complex-problems/L20260516-222011/tmp/p556/root-inventory.txt`.
- Generated keyword file list: `.complex-problems/L20260516-222011/tmp/p556/keyword-files.txt`.
- Generated module inventory: `.complex-problems/L20260516-222011/tmp/p556/module-inventory.md`.

## Verification

- Present roots:
  - `novaic-cortex`
  - `novaic-logicalfs`
  - `novaic-sandbox-service`
  - `novaic-sandbox-sdk`
  - `novaic-blob-service`
  - `novaic-agent-runtime`
  - `novaic-business`
- Missing expected standalone roots:
  - `novaic-sandbox-core` is not a separate local root.
  - `novaic-blob` is not a separate local root.
- Key files discovered:
  - Cortex: `novaic-cortex/novaic_cortex/logical_fs.py`, `workspace.py`, `sandbox.py`, `blob_payload.py`, `shell_capabilities.py`, `api.py`, `cli.py`.
  - LogicalFS: `novaic-logicalfs/logicalfs/contracts.py`, `authority.py`, `local.py`, `blob_store.py`.
  - Sandbox service/core: `novaic-sandbox-service/sandbox_service/main.py`, `core/filesystem.py`, `core/mount_namespace.py`, `core/process.py`.
  - Sandbox SDK: `novaic-sandbox-sdk/sandbox_sdk/client.py`, `contracts.py`, `types.py`.
  - Blob service: `novaic-blob-service/blob_service/main.py`, `routes.py`, `contracts.py`, `storage.py`, `blob_storage.py`, `object_storage.py`, `backends.py`.

## Known Gaps

- This inventory does not yet map import/call direction; P557 owns that.
- Separate deployed services or remote GitHub repos outside this checkout are not proven by this local inventory.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p556/root-inventory.txt`
- `.complex-problems/L20260516-222011/tmp/p556/keyword-files.txt`
- `.complex-problems/L20260516-222011/tmp/p556/module-inventory.md`

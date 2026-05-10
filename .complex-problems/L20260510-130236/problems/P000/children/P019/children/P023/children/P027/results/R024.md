# Runtime And Registry Wiring Result

## Summary

Updated active runtime wiring so registry builds a LogicalFS authority before constructing Workspace, and `Cortex.__init__` no longer exposes the old `store, agent_id` workspace construction path.

## Done

- Updated `novaic-cortex/novaic_cortex/registry.py`:
  - imports `build_workspace_file_authority`;
  - keeps per-user `BlobObjectStore` as lower object adapter;
  - creates `authority = build_workspace_file_authority(object_store, agent_id)`;
  - constructs `Workspace(authority, agent_id, ...)`.
- Updated `novaic-cortex/novaic_cortex/runtime.py`:
  - removed `CortexStore` import;
  - removed `store` and `agent_id` constructor parameters;
  - removed unused Workspace-construction collaborator parameters;
  - requires `workspace=...`.
- Verified API `_build_cortex(ws)` remains workspace-based.

## Verification

- Runtime construction smoke:
  - Constructed `MemoryStore -> build_workspace_file_authority -> Workspace -> Cortex(workspace=ws)`.
  - Result: `runtime workspace wiring ok`.
- Source scan:
  - `rg -n "CortexStore|BlobCortexStore|Workspace\\(.*store|store:|workspace_files|CortexLogicalFileAuthority" novaic-cortex/novaic_cortex/runtime.py novaic-cortex/novaic_cortex/registry.py novaic-cortex/novaic_cortex/api.py || true`
  - Result: no relevant old runtime/registry/API active-path hits.

## Known Gaps

- Many tests still call `Cortex(store, agent_id)` or `Workspace(MemoryStore(), ...)`; P028 migrates those.
- `novaic_cortex/store.py` and `workspace_files.py` still exist until final cleanup P024 decides test-only vs deletion.

## Artifacts

- `novaic-cortex/novaic_cortex/registry.py`
- `novaic-cortex/novaic_cortex/runtime.py`

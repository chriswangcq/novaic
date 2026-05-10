# P020 Audit Check

## Summary

Success for the audit problem. R019 gives a concrete active-path map, classifies direct store/blob references, identifies tests/docs affected by migration, and names the no-go dependencies that later child problems must remove. This does not close P019; it only closes the audit child.

## Evidence

- Active Workspace path evidence: `novaic-cortex/novaic_cortex/workspace.py:42-90` imports `CortexStore`, imports `CortexLogicalFileAuthority`, and constructs `self._files = CortexLogicalFileAuthority(store, agent_id)`.
- Active authority evidence: `novaic-cortex/novaic_cortex/workspace_files.py:43-175` maps logical paths to `agents/{agent_id}/...` store keys and calls `_store.put/get/list_objects/list_recursive/move_prefix`.
- Active registry evidence: `novaic-cortex/novaic_cortex/registry.py:53-77` constructs `BlobCortexStore` and passes the returned store into `Workspace`.
- Runtime compatibility evidence: `novaic-cortex/novaic_cortex/runtime.py:39-69` still supports `Cortex(store, agent_id)` as a Workspace construction path.
- LogicalFS limitation evidence: `novaic-logicalfs/logicalfs/contracts.py:1-67` and `local.py:86-171` provide snapshot/view/patch materialization, not live persistence authority.
- Shell adapter evidence: `novaic-cortex/novaic_cortex/logical_fs.py:111-243` materializes snapshots from Workspace and applies RW patches back through Workspace.

## Criteria Map

- Active Workspace/runtime/API/registry construction paths mapped: satisfied by R019 with explicit pointers to Workspace, registry, runtime, API, and shell adapter construction slices.
- Direct uses classified: satisfied by R019 classifications for `CortexLogicalFileAuthority`, `CortexStore`, `BlobCortexStore`, `ws._store`, `/v1/objects`, tests, docs, and guardrail allowlists.
- Smallest implementation slices identified: satisfied by the downstream P021-P024 split plus R019 known gaps.
- No-go hidden dependencies listed: satisfied by the R019 known gaps, especially `Workspace(store)`, live `BlobCortexStore`, `Cortex.__init__(store, agent_id)`, and broad guardrail allowlists.

## Execution Map

- Used read-only symbol scans across `novaic-cortex`, `novaic-logicalfs`, `novaic-sandbox-service`, docs, scripts, and deploy assets.
- Used targeted line-numbered source reads for files in the active construction chain.
- Recorded the audit as R019 without making implementation changes.

## Stress Test

- Checked both source and tests so test-only store usage was not mistaken for production live path.
- Checked docs and guardrail policy because stale allowlists and stale architecture language can preserve old paths even after code moves.
- Checked shell materialization separately from live persistence to avoid confusing LogicalFS view/patch substrate with live file authority.

## Residual Risk

- The audit can still miss dynamically constructed imports, but the identified active path is sufficient to drive the next implementation child problems.
- P020 leaves implementation gaps open by design; those are not P020 failures because they are represented by P021-P024.

## Result IDs

- R019

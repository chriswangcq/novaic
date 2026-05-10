# Active RO/RW Authority Audit Result

## Summary

The audit confirms the remaining live path is still Cortex-owned: `WorkspaceRegistry` constructs a `BlobCortexStore`, passes it into `Workspace`, and `Workspace` constructs `CortexLogicalFileAuthority`, which directly calls `CortexStore`. `novaic-logicalfs` is currently a shell materialization/view/patch substrate, not the live `RO` / `RW` file authority. This proves P019 is a real architectural gap, not just stale wording.

## Done

- Scanned `novaic-cortex`, `novaic-logicalfs`, `novaic-sandbox-service`, `docs`, `scripts`, and `deploy` for `CortexLogicalFileAuthority`, `CortexStore`, `BlobCortexStore`, `ws._store`, `/v1/objects`, `novaic-cortex-sandbox-*`, and LogicalFS/sandbox terms.
- Read active construction slices:
  - `novaic-cortex/novaic_cortex/workspace.py:42-90`
  - `novaic-cortex/novaic_cortex/workspace_files.py:1-175`
  - `novaic-cortex/novaic_cortex/registry.py:16-77`
  - `novaic-cortex/novaic_cortex/runtime.py:19-79`
  - `novaic-cortex/novaic_cortex/api.py:111-117`
  - `novaic-cortex/novaic_cortex/blob_store.py:1-128`
  - `novaic-logicalfs/logicalfs/contracts.py:1-67`
  - `novaic-logicalfs/logicalfs/local.py:1-171`
  - `novaic-cortex/novaic_cortex/logical_fs.py:111-243`
- Classified active dependencies:
  - `Workspace` imports `CortexStore` and constructs `CortexLogicalFileAuthority` directly.
  - `CortexLogicalFileAuthority` owns logical path mapping and direct store calls.
  - `WorkspaceRegistry` imports `CortexStore`, creates per-user `BlobCortexStore`, then creates `Workspace(store, agent_id)`.
  - `Cortex.__init__` still accepts `store` and `agent_id` to construct a `Workspace`; many tests rely on this convenience path.
  - API `_build_cortex(ws)` is already clean because it receives `workspace=ws`.
  - `MountNamespaceLogicalFS` materializes shell snapshots from `Workspace.read_tree_bytes` and writes patches back through `Workspace.write_bytes`; it does not own live persistence.
- Identified affected tests:
  - Many Cortex tests instantiate `Workspace(MemoryStore(), agent_id)` or `Cortex(MemoryStore(), agent_id)`.
  - `novaic-cortex/tests/test_blob_store.py` directly tests `BlobCortexStore`.
  - Existing guardrail allowlist explicitly permits `novaic_cortex/blob_store.py`, `registry.py`, `store.py`, and `workspace_files.py` as transitional authority files.

## Verification

- `rg -n "CortexLogicalFileAuthority|BlobCortexStore|CortexStore|ws\\._store|_store|/v1/objects|novaic-cortex-sandbox-|StoreBacked|LogicalFileAuthority" ...`
- `rg -n "class Workspace|def __init__|def get_workspace|def _get_store|def _build_cortex|class Cortex|Cortex\\(" novaic-cortex/novaic_cortex novaic-cortex/tests -g '*.py'`
- `rg -n "logicalfs|sandboxd|sandbox_process_runner|CORTEX_SANDBOXD_URL|agentctl|/cortex/ro|/cortex/rw|\\$RO|\\$RW" ...`
- Targeted `nl -ba` reads of the active files listed above.

## Known Gaps

- `novaic-logicalfs` needs a generic live file authority and object-store adapter contract; it currently has only snapshot/view/patch contracts.
- `BlobCortexStore` is live through `WorkspaceRegistry`; it must move below the LogicalFS boundary or be replaced by a LogicalFS-owned generic adapter.
- `Workspace` must stop accepting direct `CortexStore` in the active constructor.
- `Cortex.__init__(store, agent_id)` is a compatibility path used heavily by tests and should be replaced with explicit test helpers or factory methods.
- `novaic_cortex/workspace_files.py` is the current in-process authority and must be removed or made unreachable from production.
- Guardrail allowlists currently bless the transitional files; they must be tightened after cutover.

## Artifacts

- Ticket: `.complex-problems/L20260510-130236/problems/P000/children/P019/children/P020/tickets/T020.md`
- Audit body: `.complex-problems/logicalfs-p020-result.md`

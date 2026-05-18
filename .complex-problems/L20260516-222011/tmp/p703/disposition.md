# Foundational Boundary Residue Disposition

## Active cleanup candidates for P704

1. `docs/runtime/tool-chain-dispatch.md:18`
   - Current text: `Cortex owns scope/context/sandbox; Runtime performs the dispatch decision.`
   - Problem: this collapses Cortex shell orchestration with Sandboxd execution ownership. The current boundary maps say Cortex owns scope/context/shell semantics, while sandboxd owns process execution.
   - Disposition: active-cleanup.

2. `novaic-cortex/requirements.txt:8-11`
   - Current text says Redis is optional and safe to leave uninstalled if Cortex runs with the default in-memory backend.
   - Problem: current `scope_locks.py` states Cortex requires a distributed scope-lock backend and refuses to serve without it. This is not purely foundational FS, but it is an active dependency-boundary residue discovered during the fallback scan.
   - Disposition: active-cleanup.

## Acceptable current-state / no cleanup

- `novaic-cortex/novaic_cortex/logical_fs.py:3`: Cortex owns Workspace semantics and applying RW patches. This is current-state orchestration over LogicalFS substrate and is not misleading if read with the module docstring.
- `novaic-cortex/novaic_cortex/sandbox.py:7-10`: sandboxd SDK client owns remote process execution and no local path adapter exists. This is correct.
- `novaic-cortex/novaic_cortex/blob_payload.py:3`: Cortex owns work trace semantics, Blob owns large raw bytes. This is correct.
- `novaic-logicalfs/logicalfs/blob_store.py:3`: LogicalFS owns realtime `/ro` and `/rw` authority above Blob. This is correct.
- `docs/reference/blob-service.md:51` and `docs/architecture/logicalfs-realtime-file-authority.md` display/download wording: correct boundary statement.
- `docs/cortex/object-keys.md`: current boundary map looks aligned with Blob/LogicalFS/Sandbox split.

## Intentional future-gap / history

- `docs/architecture/logicalfs-realtime-file-authority.md`: explicitly says LogicalFS is not yet standalone and describes target migration phases. This is a live design document, not stale residue.
- `docs/cortex/state-authority-implementation-plan.md`: contains construction-phase language about Cortex-local SQLite substrate; this is a state-authority plan, not a foundational file/sandbox residue to patch in P704.

## Guard/test noise

- `guard-history-scan.txt` has many matches because it intentionally includes tests/docs/guard rules containing boundary terms. These are evidence surfaces, not automatic cleanup targets.

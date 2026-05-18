# LogicalFS Boundary Map

## Classification

LogicalFS is the foundational realtime logical file authority for Cortex/shell `RO` and `RW` semantics. It owns snapshot/view/patch mechanics, stable logical path layout, writable directory semantics, and the object-key authority layer above Blob.

Current implementation status: `novaic-logicalfs` is a business-agnostic Python package/substrate, not a standalone HTTP/RPC service process today. The architecture docs explicitly call out this current gap and describe promotion from library to service boundary as a future migration phase.

## Entrypoint / Module Evidence

- `novaic-logicalfs/README.md`: describes LogicalFS as a business-agnostic substrate that turns explicit snapshots into local filesystem views and RW changes into explicit patches. It says LogicalFS does not know Cortex, agents, subagents, agentctl, or process execution.
- `novaic-logicalfs/logicalfs/__init__.py`: exports `LocalLogicalFSProvider`, `LogicalFSSnapshot`, `LogicalFSLayout`, `LogicalFSPatch`, `LogicalFSView`, `StoreBackedLogicalFileAuthority`, and `BlobObjectStore`.
- `novaic-logicalfs/pyproject.toml`: package metadata and tests; no console script or service process entrypoint is defined.

## Launch / Deployment Evidence

- `scripts/start.sh` does not launch a separate LogicalFS daemon. It puts `novaic-logicalfs` on Cortex `PYTHONPATH` so Cortex can use the substrate.
- `scripts/run_all_tests.sh` runs LogicalFS tests as a separate module with explicit Python path dependencies.
- `docs/architecture/logicalfs-realtime-file-authority.md` states that LogicalFS is not yet a standalone service boundary and lists promotion from library to service boundary as a future phase.

## Dependency Boundary

- Blob is below LogicalFS as cheap durable byte/object storage. `logicalfs/blob_store.py` is an adapter over Blob Service object APIs, not a substitute for live RO/RW authority.
- Cortex currently contains `MountNamespaceLogicalFS` in `novaic-cortex/novaic_cortex/logical_fs.py`. That code adapts Cortex Workspace semantics into LogicalFS snapshots and writes RW patches back to Workspace. It is Cortex orchestration around a LogicalFS substrate, not proof that LogicalFS is a separate service process today.
- Sandboxd executes over materialized views; it does not decide logical file ownership.

## Residue Disposition

No safe docs patch was required in this ticket. The high-signal architecture doc already distinguishes current implementation from target service boundary. The important residual gap is architectural rather than stale residue: LogicalFS is not yet a standalone service process.

## Verification

- `cd novaic-logicalfs && PYTHONPATH=.:../novaic-common:../novaic-blob-service python3 -m pytest -q` passed.
- `python3 -m py_compile` passed for LogicalFS core files and Cortex LogicalFS adapter files.

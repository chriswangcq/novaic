# Result: P710 Cortex boundary discovery and map

## Summary
Cortex has been classified as the semantic state/context/scope service. It owns context/scope/event/projection semantics and shell orchestration, while consuming Blob, LogicalFS, Sandboxd, Redis, SQLite, Queue, and Runtime through explicit boundaries.

## Artifacts
- `.complex-problems/L20260516-222011/tmp/p710/boundary-map.md`
- `.complex-problems/L20260516-222011/tmp/p710/file-tree.txt`
- `.complex-problems/L20260516-222011/tmp/p710/entrypoint-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p710/launch-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p710/dependency-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p710/scan-commands.md`

## Key Evidence
- `novaic-cortex/novaic_cortex/main_cortex.py` is the uvicorn entrypoint and requires explicit `--blob-service-url`, `--sandboxd-url`, `--cortex-api-url`, `--operational-sqlite-path`, and `--redis-url`.
- `novaic-cortex/novaic_cortex/api.py` defines the FastAPI Cortex service and context/scope APIs.
- `novaic-cortex/novaic_cortex/sandbox.py` states shell execution goes through LogicalFS view acquisition plus sandboxd SDK process execution, with no local fallback.
- `novaic-cortex/novaic_cortex/workspace_authority.py` builds LogicalFS-backed file authority by agent owner prefix.
- `novaic-cortex/novaic_cortex/context_event_store.py` and `operational_store.py` provide semantic event and operational state authority.
- `scripts/start.sh` launches Cortex and passes explicit service dependencies.

## Boundary Conclusions
- Cortex owns semantic context/scope/work-trace state and API projection.
- Cortex consumes LogicalFS for realtime logical file authority; it is not the physical or standalone LogicalFS owner.
- Cortex consumes Blob through registry/client configuration; Blob owns byte/object storage.
- Cortex consumes Sandboxd through SDK; Sandboxd owns process execution.
- Cortex does not own Queue/Runtime wake/session scheduling; workers call Cortex via `--cortex-url`.

## Verification and Caveats
- Scans were saved for entrypoints, launch references, and dependency references.
- The py_compile command attempted in execution was malformed because a zsh glob for `novaic-cortex/novaic_cortex/workspace/*.py` did not match. No implementation files were changed in P710, so this does not invalidate the boundary map, but the success check should decide whether a follow-up compile-only verification is required.

## Cleanup Candidates for P711
- `scripts/start.sh:18` compresses Cortex responsibilities as `Workspace, Sandbox`; likely should become `Workspace semantics, shell orchestration` or similar.
- `docs/architecture/service-topology.md:29` may imply Cortex owns sandbox rather than sandbox orchestration.
- Check `docs/architecture/overview.md` and `docs/architecture/data-ownership.md` for active misleading `sandbox` wording.

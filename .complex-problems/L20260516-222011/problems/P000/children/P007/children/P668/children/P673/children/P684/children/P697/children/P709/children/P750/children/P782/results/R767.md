# Active Docs Boundary Wording Patch Result

## Summary
Patched the active documentation wording for Cortex, LogicalFS, Sandboxd, and Blob boundaries. The changes are scoped to the four named docs and avoid product-code changes.

## Evidence
- `docs/architecture/logicalfs-realtime-file-authority.md` now says LogicalFS is the file-operation/view authority for realtime `RO`/`RW`, while Cortex remains semantic owner of agent/wake/scope/step/payload/workspace meaning.
- `docs/architecture/cortex.md` and `docs/cortex-architecture.md` now describe `sandbox.py` as a Cortex-side shell orchestration adapter that requests LogicalFS views and delegates execution to Sandboxd.
- `docs/architecture/data-ownership.md` now separates `Cortex semantics + LogicalFS live file authority`, Blob bytes, and Sandboxd process execution.

## Criteria Map
- Cortex semantic ownership wording: satisfied.
- LogicalFS live RO/RW file-operation/view substrate wording: satisfied.
- Sandboxd process execution infrastructure wording: satisfied.
- Blob byte/object infrastructure wording: satisfied.
- Diff scoped to listed docs: satisfied.

## Execution Map
- Patched four documentation files.
- Ran targeted stale-phrase scan:
  - `LogicalFS is the semantic authority`
  - `RO/RW file semantics: LogicalFS only`
  - `物化 workspace → shell → 回写`
  - `Cortex + LogicalFS file authority`
  - `Workspace(LogicalFS authority)`
  - `mapping between semantic owners`
- Ran `git diff --check` over the four touched docs.

## Stress Test
- The patch does not rewrite historical roadmap/ticket files.
- It avoids making LogicalFS the owner of Cortex semantics; it only owns file operations and views.
- It avoids making Sandboxd a workspace owner; it is only process execution infrastructure.

## Residual Risk
- Other docs outside this ticket may still contain historical or roadmap wording, but `P749` classified those separately and this ticket intentionally touched only active docs named by the remediation backlog.

## Result IDs
- No prior result dependency beyond `R766`.

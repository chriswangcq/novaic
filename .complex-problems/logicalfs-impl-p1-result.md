# Current path audit result

## Summary

Audited the current live `RO` / `RW` paths. The shell execution path is already
substantially cut over: Cortex builds a LogicalFS view, passes a bind-mount plan
to sandboxd through `sandbox_sdk`, and rejects local fallback execution. The
remaining architectural gap is below that facade: `Workspace` still implements
live path read/write/list/delete directly over `CortexStore`, and production
`WorkspaceRegistry` still constructs `BlobCortexStore`. LogicalFS is therefore
active for shell materialization, but it is not yet the single service authority
for all live Cortex/shell `RO` / `RW` file operations.

## Done

- Inspected active Cortex shell execution:
  - `novaic-cortex/novaic_cortex/sandbox.py:53-152` orchestrates
    `MountNamespaceLogicalFS.acquire_view`, sandboxd `execute`, and
    `logical_fs.release_view`.
  - `novaic-cortex/novaic_cortex/sandbox.py:81-90` explicitly fails when no
    sandbox executor is configured.
  - `novaic-cortex/novaic_cortex/sandbox.py:38-50` rejects leaked
    `novaic-cortex-sandbox-*` backing paths.
- Inspected LogicalFS adapter:
  - `novaic-cortex/novaic_cortex/logical_fs.py:111-243` materializes Workspace
    data into a LogicalFS view, exposes `/cortex/ro` and `/cortex/rw`, and
    applies RW patches back into Workspace.
  - `novaic-cortex/novaic_cortex/logical_fs.py:131-143` reads `/ro` and `/rw`
    trees from Workspace; `234-243` writes patch results back to Workspace.
- Inspected sandboxd boundary:
  - `novaic-sandbox-service/sandbox_service/main.py:67-93` exposes only health
    and `/v1/execute`.
  - `novaic-sandbox-service/sandbox_service/core/process.py:39-84` runs process
    specs with explicit cwd/env/timeout/mount.
  - `novaic-sandbox-sdk/sandbox_sdk/contracts.py:35-111` carries command, cwd,
    env, timeout, display_command, and optional mount; no Cortex workspace
    semantics.
- Inspected production persistence:
  - `novaic-cortex/novaic_cortex/registry.py:52-60` creates `BlobCortexStore`
    per user.
  - `novaic-cortex/novaic_cortex/blob_store.py:18-127` maps `CortexStore`
    operations directly to Blob Service `/v1/objects`.
  - `novaic-cortex/novaic_cortex/workspace.py:157-264` implements public and
    system file operations directly on `_store`.
- Inspected existing tests:
  - `novaic-cortex/tests/test_sandboxd_wiring.py:42-128` proves shell requests
    pass raw command plus LogicalFS mount plan and persist RW patch writes.
  - `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py:10-25`
    proves no local fallback without sandboxd executor.

## Verification

- Used focused `rg` scans over `novaic-cortex`, `novaic-logicalfs`,
  `novaic-sandbox-service`, `novaic-sandbox-sdk`, deployment scripts, and docs.
- Read source files with line numbers for shell, LogicalFS, Workspace,
  BlobCortexStore, registry, sandboxd, SDK, and tests.
- Classified direct Blob payload/media reads as allowed cheap-byte uses when
  they operate on `blob://...` payload/audio/display bytes rather than live
  `RO` / `RW` file semantics.

## Known Gaps

- Blocking for final target: `Workspace` remains the live file-operation surface
  over `CortexStore`; LogicalFS calls into Workspace instead of being the
  authoritative service boundary.
- Blocking for final target: production registry creates `BlobCortexStore`
  directly for Cortex workspace persistence. The docs correctly label this as
  transitional, but code still uses it.
- Missing guardrail: no architecture test currently fails new direct live
  `RO` / `RW` Blob object bypasses outside LogicalFS internals.
- Sandboxd looks process-only, but P003 should still add/verify residue scans
  so that boundary does not regress.

## Artifacts

- Source pointers above.
- Follow-up implementation work is represented by child problems P002-P005.

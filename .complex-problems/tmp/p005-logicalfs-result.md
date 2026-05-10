# LogicalFS Live State Direction Plan

## Summary

Treat current snapshot/patch as a transitional adapter, not the perfect final form. The target is a live LogicalFS service with immediate durable file operations, no explicit commit, SQLite metadata/journal, and Blob-backed large bytes.

## Done

- Target service model:
  - LogicalFS service owns `/ro` and `/rw` logical namespace semantics.
  - SQLite stores inode/path metadata, versions, small file bytes, delta journal, leases, and view generations.
  - Blob stores large file bytes and immutable artifact bodies.
  - Sandbox mounts or proxies a live view; writes become immediate LogicalFS operations.
- No commit:
  - Every write/rename/delete is durable when operation returns.
  - Shell process crash leaves the last successful operation visible.
  - No release-time patch is needed for correctness.
- Concurrency:
  - RW layout remains `public`, `subagents/{id}`, `tmp`, `artifacts`, `scratch`.
  - Per-path/version conflict detection.
  - Public RW writes require compare-and-swap or serialized operation queue.
  - Subagent-private dirs avoid most conflicts.
- Cortex relation:
  - Cortex asks LogicalFS for workspace views; it does not implement FS storage.
  - Cortex writes semantic events/state to SQLite operational ledger; LogicalFS stores files.
  - Display/download use Blob for artifact bytes, referenced through manifests.
- Migration phases:
  - Phase 1: add LogicalFS live metadata API behind service.
  - Phase 2: shell writes use live operations while old snapshot/patch still shadows.
  - Phase 3: compare live state with patch output in tests.
  - Phase 4: remove release patch as authority; keep read-only export for debug if needed.
  - Phase 5: delete temp backing path assumptions and fallback code.
- Tests:
  - Write appears during running shell before process exits.
  - Kill shell after write: file persists.
  - Concurrent subagents write private dirs without conflict.
  - Concurrent public writes require CAS/serialization.
  - Large file path stores bytes in Blob and metadata in SQLite.

## Verification

- Satisfies no explicit commit requirement.
- Avoids pretending snapshot/patch is the perfect final model.

## Known Gaps

- This is a substantial implementation program and must be ticketed separately.

## Artifacts

- `.complex-problems/tmp/p005-logicalfs-result.md`


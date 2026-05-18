# Audit Docs for Blob/Workspace Authority Wording result

## Summary

Audited docs for Blob/Workspace authority wording. The current architecture docs mostly already state the intended boundary: LogicalFS/Workspace owns live RO/RW semantics and Blob stores cheap bytes/object payloads. Two doc residues were patched.

## Changes Made

- `docs/architecture/data-ownership.md`: changed “HTTP 默认 19996” to explicit service endpoint wording and recorded that shell capability must not use implicit localhost fallback.
- `docs/roadmap/tickets/PR-202-cortex-payload-blob-externalization.md`: added a closed-ticket banner clarifying that its “Current-State Analysis” is historical baseline, while current runtime behavior stores Cortex payload meaning/manifests and externalizes only large raw bytes behind explicit BlobRefs.

## Classification

- `docs/architecture/logicalfs-realtime-file-authority.md`, `docs/reference/blob-service.md`, `docs/cortex/object-keys.md`: current and correct boundary docs.
- `docs/roadmap/tickets/PR-207-cortex-blob-store-cutover.md`: historical ticket already has a warning banner that current architecture uses LogicalFS as live RO/RW authority.
- `docs/roadmap/tickets/PR-202-cortex-payload-blob-externalization.md`: was potentially misleading because it used “Current-State Analysis” without a closed-ticket baseline note; patched.
- Roadmap ticket index lines are historical backlog metadata, not live architecture guidance.

## Verification

- Broad docs scan: `.complex-problems/L20260516-222011/tmp/P654-docs-blob-scan.txt`.
- High-risk docs scan: `.complex-problems/L20260516-222011/tmp/P654-docs-high-risk-scan-rerun.txt`.
- Postscan after patches: `.complex-problems/L20260516-222011/tmp/P654-docs-postscan-rerun.txt`.
- Postscan no longer contains the stale “HTTP 默认 19996” phrase; PR-202 now explicitly marks its Current-State Analysis as pre-implementation baseline.

## Residual Risk

Low. Historical roadmap tickets still contain terms like `BlobCortexStore`, but the high-risk closed ticket PR-207 already has a current-architecture warning banner. A repo-wide archival banner cleanup for every old roadmap ticket would be a separate documentation hygiene problem, not this Blob authority boundary.

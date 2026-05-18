# Active Docs Boundary Wording Patch Ticket

## Problem Definition

Patch the active architecture docs named by discovery so they no longer blur Cortex semantic ownership, LogicalFS live RO/RW file-operation authority, Sandboxd execution, and Blob byte ownership.

## Proposed Solution

Inspect and patch only the documented files:

- `docs/architecture/logicalfs-realtime-file-authority.md`
- `docs/architecture/cortex.md`
- `docs/cortex-architecture.md`
- `docs/architecture/data-ownership.md`

Use conservative wording updates. Do not rewrite unrelated historical or roadmap material.

## Acceptance Criteria

- Cortex is described as owning scope/context/workspace semantics.
- LogicalFS is described as the live RO/RW file-operation/view substrate, not the semantic owner of agent state.
- Sandboxd is described as process/sandbox execution infrastructure.
- Blob is described as byte/object storage infrastructure.
- Diff is wording-only and scoped to the listed files.

## Verification Plan

Run targeted `rg` checks for stale phrases after patching and inspect `git diff -- docs/architecture/logicalfs-realtime-file-authority.md docs/architecture/cortex.md docs/cortex-architecture.md docs/architecture/data-ownership.md`.

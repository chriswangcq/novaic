# Implement Generic LogicalFS Live Authority

## Problem Definition

`novaic-logicalfs` currently owns local view materialization and patch detection, but live `RO` / `RW` persistence authority still lives in Cortex. P021 must add a business-independent LogicalFS authority layer so later Cortex work can depend on LogicalFS rather than an in-process Cortex-specific authority.

## Proposed Solution

Add generic authority contracts and an object-store-backed implementation inside `novaic-logicalfs`. The implementation should accept explicit owner prefix/layout configuration, expose logical path read/write/list/delete/append/move operations, and return LogicalFS-owned directory entry types. Add in-memory test adapter coverage without importing `novaic-cortex`.

## Acceptance Criteria

- `novaic-logicalfs` exposes the live authority and related types from its public package API.
- The authority maps `/ro/...` and `/rw/...` through explicit config, not hard-coded Cortex agent state.
- The backing object store contract is generic and business-independent.
- Tests cover path normalization/rejection, reads/writes, directory listing, tree reads, move prefix, append, and default layout initialization.
- No `novaic_cortex` imports are introduced into `novaic-logicalfs`.

## Verification Plan

- Add focused unit tests under `novaic-logicalfs/tests`.
- Run `PYTHONPATH=.:../novaic-common python3 -m pytest -q` in `novaic-logicalfs`.
- Run a source scan to prove `novaic-logicalfs` does not import `novaic_cortex`.

## Risks

- A too-Cortex-shaped API would simply move residue into LogicalFS.
- Directory listing behavior needs to preserve enough information for Cortex Workspace to map to its existing `FileEntry` later.

## Assumptions

- The backing object store can be represented as a Protocol/duck type with async `put/get/exists/delete/list_objects/list_recursive/move_prefix`.
- Blob adapter cutover is handled by P022, not this ticket.

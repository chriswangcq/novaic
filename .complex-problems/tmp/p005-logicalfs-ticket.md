# Design LogicalFS Live State Direction

## Problem Definition

LogicalFS currently materializes a snapshot for shell and applies patches on release. The user prefers realtime LogicalFS semantics and dislikes explicit commit. Need a plan that avoids half-implemented live FS and clarifies whether snapshot/patch is acceptable.

## Proposed Solution

Define a staged live LogicalFS model with SQLite metadata/delta journal and Blob byte storage, while keeping snapshot/patch only as a compatibility execution adapter until live mounting is ready.

## Acceptance Criteria

- State whether snapshot/patch is final or transitional.
- Define live LogicalFS write/read semantics without commit.
- Include crash recovery, concurrency, and subagent RW layout.
- Define deletion of compatibility logic once live path is active.

## Verification Plan

Check shell write immediacy, crash during execution, concurrent subagent isolation, and no fallback to temp backing paths.

## Risks

- Live FS is a bigger subsystem; doing it halfway creates worse bugs than snapshot/patch.
- Per-op writes can be slow without batching/caching.

## Assumptions

- LogicalFS can use SQLite for metadata/journal and Blob for larger bytes.


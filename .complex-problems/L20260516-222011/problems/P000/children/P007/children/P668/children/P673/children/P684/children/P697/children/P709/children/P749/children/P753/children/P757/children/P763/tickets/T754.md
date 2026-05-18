# LogicalFS residue discovery ticket

## Problem Definition

LogicalFS code may contain stale fallback, compatibility, local-only, commit/writeback, or ownership wording that conflicts with LogicalFS as the realtime logical RO/RW file authority above Blob.

## Proposed Solution

Scan LogicalFS source, tests, docs, and scripts for residue terms, inspect representative hits, and classify each high-signal group as current realtime file authority behavior, adapter boundary, stale remediation candidate, or unrelated vocabulary.

## Acceptance Criteria

- LogicalFS source and tests are discovered.
- Suspicious hits are classified with file pointers.
- Remediation candidates are listed or absence is recorded.
- No product code is modified in this discovery child.

## Verification Plan

Use `rg --files novaic-logicalfs` and focused `rg` searches for fallback/compat/local/direct/base64/media/artifact/blob/storage/logicalfs/commit/writeback/ro/rw terms. Spot-read high-signal files and tests before recording the result.

## Risks

- LogicalFS is supposed to own realtime RO/RW file semantics, so words such as `local`, `storage`, `blob`, `mount`, `write`, or `rw` are not automatically stale.
- The discovery child should not patch product code; remediation belongs to a later parent remediation ticket if candidates are found.

## Assumptions

- Active LogicalFS code is under `novaic-logicalfs`.

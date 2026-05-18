# LogicalFS residue discovery

## Problem

Scan LogicalFS code for stale fallback, compatibility, local-only, commit/writeback, or ownership wording that conflicts with LogicalFS as the realtime logical RO/RW file authority above Blob. This belongs under P757 because LogicalFS is the realtime file layer in the current architecture.

## Success Criteria

- LogicalFS source files are discovered and scanned with bounded commands.
- Suspicious hits are classified as current realtime file authority behavior, adapter boundary, stale residue, or unrelated vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.

# Audit Docs for Blob/Workspace Authority Wording

## Problem

Docs may still describe Blob as the live Cortex workspace authority, which can mislead future implementation even when code is clean.

## Success Criteria

- Scan architecture/docs/runbooks for Blob + Workspace/LogicalFS/Cortex wording.
- Preserve docs that correctly describe Blob as cheap durable file/artifact storage.
- Update or spawn follow-up for docs that imply Blob owns live `/ro`/`/rw` semantics or bypasses LogicalFS/Workspace.

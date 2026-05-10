# Clean Blob boundary and live RO/RW bypasses

## Problem

Blob remains a cheap byte/object file server. Direct Blob access is allowed for
attachments, display bytes, artifact bytes, downloads, and LogicalFS persistence
internals. It must not remain as a live Cortex/shell `RO` / `RW` authority or
hidden fallback path.

## Success Criteria

- Direct Blob object calls are audited and either accepted as cheap-byte use or
  moved behind LogicalFS for live `RO` / `RW`.
- Tests or guard scripts fail on new direct live `RO` / `RW` Blob bypasses.
- Documentation and code comments do not imply Blob owns live workspace
  semantics.
- No display/download path depends on LogicalFS handles.

# Legacy and standalone media-byte surface classification

## Problem

Classify remaining screenshot/image/base64-producing surfaces, especially standalone MCP/plugin code such as `novaic-mcp-vmuse`, so legitimate non-shell media APIs are not confused with active shell/runtime context behavior.

## Success Criteria

- Remaining media-byte or image-content emitting code paths are listed with file pointers.
- Each path is classified as active shell/runtime, standalone plugin/MCP, test fixture, doc, or obsolete residue.
- Active violations are forwarded to remediation candidates.
- Obsolete or misleading residue candidates are forwarded to remediation candidates for deletion or doc correction.

# VMuse delete FastMCP main module

## Problem
Remove the stale source `main.py` FastMCP module that directly returns MCP image content and is no longer the active service entry.

## Success Criteria
- `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py` is physically deleted.
- No source VMuse import still requires `novaic_mcp_vmuse.main` after deletion.
- Deletion preserves unrelated existing changes in other VMuse files.

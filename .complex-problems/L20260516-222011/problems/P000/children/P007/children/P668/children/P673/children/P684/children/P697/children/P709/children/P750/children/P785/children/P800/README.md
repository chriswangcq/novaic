# App VMuse resource copy sync

## Problem
`novaic-app/src-tauri/resources/novaic-mcp-vmuse` is a committed VMuse copy that can drift from source VMuse cleanup and still carry stale FastMCP/direct-media code.

## Success Criteria
- App resource VMuse copy matches source VMuse for cleaned source files or is explicitly removed if it should not be committed.
- No stale FastMCP/SSE/stdio/direct-media markers remain in the app resource VMuse copy.
- A focused diff/scan proves resource copy consistency.

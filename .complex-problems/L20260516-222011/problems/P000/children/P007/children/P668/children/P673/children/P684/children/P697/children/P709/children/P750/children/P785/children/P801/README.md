# App generated VMuse asset copy sync

## Problem
`novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse` is a generated/committed VMuse copy that can still contain stale FastMCP/direct-media code after source cleanup.

## Success Criteria
- Generated Apple VMuse asset copy matches the cleaned app resource/source contract or is explicitly deleted if generated assets should not be committed.
- No stale FastMCP/SSE/stdio/direct-media markers remain in generated VMuse assets.
- A focused scan covers generated asset paths.

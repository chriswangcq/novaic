# MCP scripts shell adapter residue scan

## Problem

MCP adapter and scripts may still expose old direct tool names, fallback shell behavior, base64 media text, or stale compatibility comments after the shell/blob/display contract change.

## Success Criteria

- Focused scans cover `novaic-mcp-vmuse` and relevant top-level scripts for legacy, fallback, compat, migration, TODO/FIXME, direct tool names, base64, and blob/display terms.
- Hits are classified as active adapter path, test fixture, intentional guard, or stale residue.
- Safe tiny cleanup is applied directly if found.
- Focused MCP/script checks pass or no-code-change verification is explicit.

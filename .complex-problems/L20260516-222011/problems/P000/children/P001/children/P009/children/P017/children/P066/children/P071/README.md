# App business MCP adapter fallback compatibility residue scan

## Problem

App, business, and MCP adapter code may still preserve old direct-tool, fallback, or compatibility branches that are no longer part of the current shell/CLI-facing architecture.

## Success Criteria

- Focused scans cover `novaic-app`, `novaic-business`, `novaic-mcp-vmuse`, and scripts for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, and direct-tool residue.
- Hits are classified as active risk, intentional UI/test compatibility, benign adapter, or stale residue.
- Safe tiny cleanup is applied directly if discovered.
- Touched areas receive focused tests/lint or explicit no-code-change verification.

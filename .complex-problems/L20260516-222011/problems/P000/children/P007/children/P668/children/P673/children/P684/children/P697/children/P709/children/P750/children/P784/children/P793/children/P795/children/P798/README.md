# VMuse CLI and package metadata HTTP contract

## Problem
After deleting the FastMCP module, source CLI/package comments must point to the HTTP server contract and stop advertising FastMCP/SSE/stdio entry behavior.

## Success Criteria
- Source CLI `serve` delegates to `novaic_mcp_vmuse.http_server.main` or equivalent HTTP server entry.
- Source CLI/info/version output no longer mentions FastMCP, SSE, stdio, or `.main import mcp`.
- Source package comments no longer tell callers to import `mcp` from `.main`.
- Package metadata remains installable with the `novaic` console script.

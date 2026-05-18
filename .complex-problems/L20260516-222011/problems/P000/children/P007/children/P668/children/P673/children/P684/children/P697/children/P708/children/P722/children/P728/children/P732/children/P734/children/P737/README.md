# Classify VMuse HTTP and file binary API surfaces

## Problem

Classify `novaic-mcp-vmuse` HTTP server and file binary APIs that expose or accept base64 content. These may be legitimate standalone transport APIs, but they should not be mistaken for the active shell/display contract.

## Success Criteria

- HTTP screenshot endpoints in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py` are classified with file pointers.
- Binary file pull/push paths in `tools/files.py` and `http_server.py` are classified with file pointers.
- The result states whether each API is standalone compatibility, active shell/runtime, or remediation candidate.
- Exact cleanup/remediation candidates are listed if any path is stale or contract-violating.

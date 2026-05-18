# Complete residual production media-byte classification

## Problem

Close the remaining gaps in the active non-test media-byte surface classification. Re-scan the production code hits, inspect each remaining unclassified surface, and decide whether each path is active shell/runtime, current-round display/provider transport, standalone MCP/plugin, internal encoding, legacy compatibility, or remediation candidate. In particular, resolve `novaic-device/device/vmcontrol_routes.py`, all `novaic-mcp-vmuse` screenshot/file/base64 surfaces, and any smaller missed hits such as `tools/windows.py`.

## Success Criteria

- Every remaining non-test media-byte/base64 hit from the production scan is either classified with a file pointer or explicitly declared irrelevant with evidence.
- `novaic-device/device/vmcontrol_routes.py` screenshot route has a clear status: active product path, legacy compatibility, safe-to-retire, or remediation candidate.
- `novaic-mcp-vmuse` media/file base64 surfaces are classified by module rather than only as a broad package.
- The final result lists exact remediation candidates for the parent cleanup phase.

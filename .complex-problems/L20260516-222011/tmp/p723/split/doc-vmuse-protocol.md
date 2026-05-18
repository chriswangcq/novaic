# Update stale VMuse protocol mapping documentation

## Summary

Patch `docs/mcp-vmuse/mcp-protocol-mapping.md` so it no longer describes direct Runtime-to-LLM VMuse MCP media exposure as the live design.

## Problem

Discovery found the doc can mislead future work into reintroducing direct MCP/media tool exposure. The current design is shell/device proxy for action, Blob/tool-output manifests for shell text, and explicit `display` for current-round visual perception.

## Success Criteria

- The doc clearly marks old direct MCP exposure material as historical or replaces it with the current shell/device-proxy boundary.
- The doc states that shell/history must not carry raw base64/media bytes as text.
- The doc points to Blob manifests and display projection as the current contract.
- Documentation-only checks or a targeted grep confirm no stale live-design claim remains in that file.

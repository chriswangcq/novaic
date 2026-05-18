# Classify VMuse desktop screenshot MCP surfaces

## Problem

Classify the VMuse desktop screenshot and aim screenshot path across `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py` and `tools/desktop.py`. These paths base64-encode screenshots and convert them to FastMCP image content, and need a clear boundary status.

## Success Criteria

- `main.py` desktop screenshot and mouse aim wrappers are inspected with file/function pointers.
- `tools/desktop.py` screenshot and aim result construction are inspected with file/function pointers.
- The result states whether these are standalone MCP image transport, current shell/runtime behavior, or remediation candidates.
- Dead or misleading comments/imports found in this path are listed.

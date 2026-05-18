# Classify VMuse MCP tool media-byte surfaces

## Problem

Classify media/base64 output paths in the standalone `novaic-mcp-vmuse` MCP tool layer, especially `main.py`, `tools/desktop.py`, `tools/browser.py`, and any small missed imports such as `tools/windows.py`. We need to separate legitimate MCP image transport from shell/runtime history contract violations.

## Success Criteria

- Each MCP tool module with base64/image hits is inspected and classified with file pointers.
- Screenshot, aim screenshot, browser screenshot, and window/media-related base64 surfaces are classified by function or module.
- The result states whether the surfaces are standalone MCP/plugin behavior, active runtime shell behavior, or remediation candidates.
- Any dead or misleading imports are listed as cleanup candidates.

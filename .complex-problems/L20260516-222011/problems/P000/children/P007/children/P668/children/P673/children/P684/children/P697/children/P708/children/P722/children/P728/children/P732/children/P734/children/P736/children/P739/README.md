# Classify VMuse browser and window MCP media surfaces

## Problem

Classify VMuse browser screenshot and window/misc media-byte surfaces, especially `tools/browser.py`, `main.py` browser screenshot wrapper, and `tools/windows.py` base64 usage/imports.

## Success Criteria

- Browser screenshot encode/decode/wrapper path is inspected with file/function pointers.
- `tools/windows.py` base64 usage/import status is inspected and classified.
- The result states whether each path is standalone MCP/plugin behavior, active shell/runtime behavior, dead code/import residue, or remediation candidate.
- Exact cleanup candidates are listed.
